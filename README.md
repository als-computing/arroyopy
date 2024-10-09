# Arroyo Stream Processing Toolset

Processing event or streaming data presents several technological challenges. A variety of technologies are often used by scientific user facilities. ZMQ is used to stream data and messages in a peer-to-peer fashion. Message brokers like Kafka, Redis and RabbitMQ are often employed to route and pass messages from instruments to processing workflows. Arroyo provides an API and structure to flexibly integrate with these tools and incorporate arbitrarily complex processing workflows, letting the hooks to the workflow code be independent of the connection code and hence reusable at a variety of instruments. 

The basic structure of building an arroyo implementation is to implement groups of several  classes:
- 
- `Operator` - receives `Messages` from a listener and can optionally send `Messages` to one or more `Publisher` instances
- `Listener` - receives `Messages` from the external world, parse them into arroyo `Message` and sends them to an `Operator`
- `Publisher` - receives `Messages` from a `Listener` and publishes them to the outside world




Arroyo is un-opinionated about deployment decsions. It is intended support listener-operator-publisher groups in:
- Single process
- Chain of processes where listening, processing and publishing can linked together through a protocol like ZMQ. One process's publisher can communicate with another process's listener, etc.

This library is intended to provide  classes, and will also include more specific common subclasses, like those that communicate over ZMQ or Redis.



```mermaid

---
title: Some sweet classes

note: I guess we use "None" instead of "void"
---

classDiagram
    namespace listener{

        class Listener{
            operator: Operator

            *start(): None  
            *stop(): None
        }

        
    }

    namespace operator{
        class Operator{
            publisher: List[Publisher]
            *process(Message): None
            add_publisher(Publisher): None
            remove_publisher(Publisher): None

        }
    }

    namespace publisher{
        class Publisher{
            *publish(Message): None
        }

    }

    namespace message{
        
        class Message{

        }

        class Start{
            data: Dict
        }
    
        class Stop{
            data: Dict
        }

        class Event{
            metadata: Dict
            payload: bytes
        }
    }
 
    namespace zmq{
        class ZMQListener{
            operator: Operator
            socket: zmq.Socket
        }

        class ZMQPublisher{
            host: str
            port: int
        }

    }

    namespace redis{

        class RedisListener{
            operator: Redis.client
            pubsub: Redis.pubsub
        }

        class RedisPublisher{
            pubsub: Redis.pubsub
        }

    }

 

    Listener <|-- ZMQListener
    ZMQListener <|-- ZMQPubSubListener
    Listener o-- Operator

    Publisher <|-- ZMQPublisher
    ZMQPublisher <|-- ZMQPubSubPublisher

    Publisher <|-- RedisPublisher
    Listener <|-- RedisListener
    Operator o-- Publisher
    Message <|-- Start
    Message <|-- Stop
    Message <|-- Event 
    
     
```
##
In-process, listening for ZMQ

Note that this leaves Concrete classes undefined as placeholders

TODO: parent class labels

```mermaid

sequenceDiagram
    autonumber
    ExternalPublisher ->> ZMQPubSubListener: publish(bytes)
    loop receiving thread
        activate ZMQPubSubListener
            ZMQPubSubListener ->> ConcreteMessageParser: parse(bytes)
            ZMQPubSubListener ->> MessageQueue: put(bytes)
        deactivate ZMQPubSubListener

        
        ZMQPubSubListener ->> MessageQueue: message(Message)
    end
    activate ConcreteOperator
        loop polling thread
            ConcreteOperator ->> MessageQueue: get(bytes)
        end
        loop processing thread
            ConcreteOperator ->> ConcreteOperator: calculate()
        
            ConcreteOperator ->> ConcretePublisher: publish()
        end
    deactivate ConcreteOperator
```

