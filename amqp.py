import time
import os
import pika
import json
import tornado
import tornado.websocket as websocket
from pika.adapters.tornado_connection import TornadoConnection
import datetime
import traceback


class Log(object):
    def __init__(self,logname,log_to_console=False):
        self.log_to_console = log_to_console
        self._logname = logname
    
    def time_now(self):
        return datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    
    def log(self,entry):
        if self.log_to_console:
            print self.time_now()+': '+entry
            return
        with open(self.logname(),'a') as f:
            f.write('\n'+self.time_now()+': '+entry+'\n')
    
    def logname(self):
        return self._logname+'.log'

    def clear(self):
        with open(self.logname(),'w') as f:
            f.write('')

class AMQPHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self, *args, **kwargs):
        self.application.pc.add_event_listener(self)
        self.application.pc._channel.basic_consume(
            self.consume,
            queue=self.application.pc.QUEUE,
            no_ack=True
        )

    def on_close(self, *args, **kwargs):
        self.application.pc.remove_event_listener(self)
    
    def send_message(self,message):
        while True:
            try:
                self.write_message(message)
                break
            except tornado.websocket.WebSocketClosedError:
                time.sleep(1)
            
   
    @tornado.web.asynchronous
    def on_message(self,message):
        _json = json.loads(message)
        actions = {
            "publish":self.publish
        }
        try:
            actions[_json['action']](_json,message)
        except:
            self.pc.log.log(traceback.format_exc())
        
    def publish(self,_json,message):
        self.application.pc._channel.basic_publish(_json['exchange'],_json['routing_key'],message)

    def consume(self,ch,method,properties,body):
        self.send_message(body)

class PikaClient(object):
    """This is an example consumer that will handle unexpected interactions
    with RabbitMQ such as channel and connection closures.

    If RabbitMQ closes the connection, it will reopen it. You should
    look at the output, as there are limited reasons why the connection may
    be closed, which usually are tied to permission related issues or
    socket timeouts.

    If the channel is closed, it will indicate a problem with one of the
    commands that were issued and that should surface in the output as well.

    """
    EXCHANGE = 'message'
    EXCHANGE_TYPE = 'topic'
    QUEUE = 'test'
    ROUTING_KEY = 'message.test'

    def __init__(self, amqp_url,log):
        self._connection = None
        self._channel = None
        self._closing = False
        self._consumer_tag = None
        self._url = amqp_url
        self.log = log
        self.event_listeners = set([])

    def connect(self):
        self.log.log('Connecting to %s' % self._url)
        return adapters.TornadoConnection(pika.URLParameters(self._url),
                                          self.on_connection_open,stop_ioloop_on_close=False)

    def close_connection(self):
        self.log.log('Closing connection')
        self._connection.close()

    def add_on_connection_close_callback(self):
        """This method adds an on close callback that will be invoked by pika
        when RabbitMQ closes the connection to the publisher unexpectedly.

        """
        self.log.log('Adding connection close callback')
        self._connection.add_on_close_callback(self.on_connection_closed)

    def on_connection_closed(self, connection, reply_code, reply_text):
        """This method is invoked by pika when the connection to RabbitMQ is
        closed unexpectedly. Since it is unexpected, we will reconnect to
        RabbitMQ if it disconnects.

        :param pika.connection.Connection connection: The closed connection obj
        :param int reply_code: The server provided reply_code if given
        :param str reply_text: The server provided reply_text if given

        """
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            self.log.log('Connection closed, reopening in 5 seconds: (%s) %s' %
                           (reply_code, reply_text))
            self._connection.add_timeout(5, self.reconnect)

    def on_connection_open(self, unused_connection):
        """This method is called by pika once the connection to RabbitMQ has
        been established. It passes the handle to the connection object in
        case we need it, but in this case, we'll just mark it unused.

        :type unused_connection: pika.SelectConnection

        """
        self.log.log('Connection opened')
        self.add_on_connection_close_callback()
        self.open_channel()

    def reconnect(self):
        """Will be invoked by the IOLoop timer if the connection is
        closed. See the on_connection_closed method.

        """
        if not self._closing:
            # Create a new connection
            self._connection = self.connect()

    def add_on_channel_close_callback(self):
        """This method tells pika to call the on_channel_closed method if
        RabbitMQ unexpectedly closes the channel.

        """
        self.log.log('Adding channel close callback')
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reply_code, reply_text):
        """Invoked by pika when RabbitMQ unexpectedly closes the channel.
        Channels are usually closed if you attempt to do something that
        violates the protocol, such as re-declare an exchange or queue with
        different parameters. In this case, we'll close the connection
        to shutdown the object.

        :param pika.channel.Channel: The closed channel
        :param int reply_code: The numeric reason the channel was closed
        :param str reply_text: The text reason the channel was closed

        """
        self.log.log('Channel %i was closed: (%s) %s' %
                       (channel, reply_code, reply_text))
        self._connection.close()

    def on_channel_open(self, channel):
        """This method is invoked by pika when the channel has been opened.
        The channel object is passed in so we can make use of it.

        Since the channel is now open, we'll declare the exchange to use.

        :param pika.channel.Channel channel: The channel object

        """
        self.log.log('Channel opened')
        self._channel = channel
        self.add_on_channel_close_callback()
        self.setup_exchange(self.EXCHANGE)

    def setup_exchange(self, exchange_name):
        """Setup the exchange on RabbitMQ by invoking the Exchange.Declare RPC
        command. When it is complete, the on_exchange_declareok method will
        be invoked by pika.

        :param str|unicode exchange_name: The name of the exchange to declare

        """
        self.log.log('Declaring exchange %s' % exchange_name)
        self._channel.exchange_declare(self.on_exchange_declareok,
                                       exchange_name,
                                       self.EXCHANGE_TYPE)

    def on_exchange_declareok(self, unused_frame):
        """Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
        command.

        :param pika.Frame.Method unused_frame: Exchange.DeclareOk response frame

        """
        self.log.log('Exchange declared')
        self.setup_queue(self.QUEUE)

    def setup_queue(self, queue_name):
        """Setup the queue on RabbitMQ by invoking the Queue.Declare RPC
        command. When it is complete, the on_queue_declareok method will
        be invoked by pika.

        :param str|unicode queue_name: The name of the queue to declare.

        """
        self.log.log('Declaring queue %s' % queue_name)
        self._channel.queue_declare(self.on_queue_declareok, queue_name)

    def on_queue_declareok(self, method_frame):
        """Method invoked by pika when the Queue.Declare RPC call made in
        setup_queue has completed. In this method we will bind the queue
        and exchange together with the routing key by issuing the Queue.Bind
        RPC command. When this command is complete, the on_bindok method will
        be invoked by pika.

        :param pika.frame.Method method_frame: The Queue.DeclareOk frame

        """
        self.log.log('Binding %s to %s with %s' %
                    (self.EXCHANGE, self.QUEUE, self.ROUTING_KEY))
        self._channel.queue_bind(self.on_bindok, self.QUEUE,
                                 self.EXCHANGE, self.ROUTING_KEY)

    def add_on_cancel_callback(self):
        """Add a callback that will be invoked if RabbitMQ cancels the consumer
        for some reason. If RabbitMQ does cancel the consumer,
        on_consumer_cancelled will be invoked by pika.

        """
        self.log.log('Adding consumer cancellation callback')
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        """Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer
        receiving messages.

        :param pika.frame.Method method_frame: The Basic.Cancel frame

        """
        self.log.log('Consumer was cancelled remotely, shutting down: %r',
                    method_frame)
        if self._channel:
            self._channel.close()

    def acknowledge_message(self, delivery_tag):
        """Acknowledge the message delivery from RabbitMQ by sending a
        Basic.Ack RPC method for the delivery tag.

        :param int delivery_tag: The delivery tag from the Basic.Deliver frame

        """
        self.log.log('Acknowledging message %s' % delivery_tag)
        self._channel.basic_ack(delivery_tag)

    def on_message(self, unused_channel, basic_deliver, properties, body):
        """Invoked by pika when a message is delivered from RabbitMQ. The
        channel is passed for your convenience. The basic_deliver object that
        is passed in carries the exchange, routing key, delivery tag and
        a redelivered flag for the message. The properties passed in is an
        instance of BasicProperties with the message properties and the body
        is the message that was sent.

        :param pika.channel.Channel unused_channel: The channel object
        :param pika.Spec.Basic.Deliver: basic_deliver method
        :param pika.Spec.BasicProperties: properties
        :param str|unicode body: The message body

        """
        self.log.log('Received message # %s from %s: %s' % 
                    (basic_deliver.delivery_tag, properties.app_id, body))
        self.notify_listeners(body)
        self.acknowledge_message(basic_deliver.delivery_tag)
        

    def on_cancelok(self, unused_frame):
        """This method is invoked by pika when RabbitMQ acknowledges the
        cancellation of a consumer. At this point we will close the channel.
        This will invoke the on_channel_closed method once the channel has been
        closed, which will in-turn close the connection.

        :param pika.frame.Method unused_frame: The Basic.CancelOk frame

        """
        self.log.log('RabbitMQ acknowledged the cancellation of the consumer')
        self.close_channel()

    def stop_consuming(self):
        """Tell RabbitMQ that you would like to stop consuming by sending the
        Basic.Cancel RPC command.

        """
        if self._channel:
            self.log.log('Sending a Basic.Cancel RPC command to RabbitMQ')
            self._channel.basic_cancel(self.on_cancelok, self._consumer_tag)

    def start_consuming(self):
        """This method sets up the consumer by first calling
        add_on_cancel_callback so that the object is notified if RabbitMQ
        cancels the consumer. It then issues the Basic.Consume RPC command
        which returns the consumer tag that is used to uniquely identify the
        consumer with RabbitMQ. We keep the value to use it when we want to
        cancel consuming. The on_message method is passed in as a callback pika
        will invoke when a message is fully received.

        """
        self.log.log('Issuing consumer related RPC commands')
        self.add_on_cancel_callback()
        self._consumer_tag = self._channel.basic_consume(self.on_message,
                                                         self.QUEUE)

    def on_bindok(self, unused_frame):
        """Invoked by pika when the Queue.Bind method has completed. At this
        point we will start consuming messages by calling start_consuming
        which will invoke the needed RPC commands to start the process.

        :param pika.frame.Method unused_frame: The Queue.BindOk response frame

        """
        self.log.log('Queue bound')
        self.start_consuming()

    def close_channel(self):
        """Call to close the channel with RabbitMQ cleanly by issuing the
        Channel.Close RPC command.

        """
        self.log.log('Closing the channel')
        self._channel.close()

    def open_channel(self):
        """Open a new channel with RabbitMQ by issuing the Channel.Open RPC
        command. When RabbitMQ responds that the channel is open, the
        on_channel_open callback will be invoked by pika.

        """
        self.log.log('Creating a new channel')
        self._connection.channel(on_open_callback=self.on_channel_open)

    def run(self):
        """Run the example consumer by connecting to RabbitMQ and then
        starting the IOLoop to block and allow the SelectConnection to operate.

        """
        self._connection = self.connect()
        self._connection.ioloop.start()

    def stop(self):
        """Cleanly shutdown the connection to RabbitMQ by stopping the consumer
        with RabbitMQ. When RabbitMQ confirms the cancellation, on_cancelok
        will be invoked by pika, which will then closing the channel and
        connection. The IOLoop is started again because this method is invoked
        when CTRL-C is pressed raising a KeyboardInterrupt exception. This
        exception stops the IOLoop which needs to be running for pika to
        communicate with RabbitMQ. All of the commands issued prior to starting
        the IOLoop will be buffered but not processed.

        """
        self.log.log('Stopping')
        self._closing = True
        self.stop_consuming()
        self._connection.ioloop.start()
        self.log.log('Stopped')

 
    def notify_listeners(self, event_obj):
        # here we assume the message the sourcing app
        # post to the message queue is in JSON format
        event_json = json.dumps(event_obj)
 
        for listener in self.event_listeners:
            listener.write_message(event_json)
            self.log.log('PikaClient: notified %s' % repr(listener))
 
    def add_event_listener(self, listener):
        self.event_listeners.add(listener)
        self.log.log('PikaClient: listener %s added' % repr(listener))
 
    def remove_event_listener(self, listener):
        try:
            self.event_listeners.remove(listener)
            self.log.log('PikaClient: listener %s removed' % repr(listener))
        except KeyError:
            pass

class BaseHandler(tornado.web.RequestHandler):
    def get(self,*args,**kwargs):
        self.render('index.html')

from optparse import OptionParser

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-d",dest="debug",action="store_false",
        help="run torando in debug mode",metavar="DEBUG",default=True)
    (options,args) = parser.parse_args()

    static_path = os.path.join(os.curdir, "static")
    app_options = {'debug':options.debug}
    app = tornado.web.Application([
        (r'/amqp',AMQPHandler),
        (r'/static/(.*)', tornado.web.StaticFileHandler, {'path':static_path}),
        (r'/',BaseHandler),
    ], **app_options)

    io_loop = tornado.ioloop.IOLoop.instance()
 
    # PikaClient is our rabbitmq consumer
    pc = PikaClient('amqp://guest:guest@localhost:5672/%2F',Log('PikaLog',operations.debug))
    pc.application = app
    app.pc = pc
    try:
        app.listen(18510)
        pc.run()
    except KeyboardInterrupt:
        pc.stop()


