# Arroyo is Spanish for stream
This is an initial design for a library intended to be used in a variety of streaming processing scenario.


This is intended to provide classes that can be used in a wide variety of processing scenarios
- Single process
- Chain of processes where listening, processing and publishing can linked together through a protocol like ZMQ. One process's publisher can communicate with another process's listener, etc.

This library is intended to provide abstract classes, and will also include more specific common subclasses, like those that communicate over ZMQ.



```mermaid
---
title: Some sweet classes

note: I guess we use "None" instead of "void"
---

classDiagram

    class AbstractListener{
        operator: AbstractOperator
        parser: AbstractMessageParser
        start(): None  
        stop(): None
    }


    class AbstractOperator{
        publisher: AbstractPublisher
        receive(Event): None
        publish(Event): None

    }

    class AbstractPublisher{
        publish(): None
    }

    class Message{

    }

   class ZMQPublisher{
        host: str
        port: int
    }

    class ZMQPubSubPublisher{

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

    class ZMQListener{
        host: str
        port: int
    }

    class ZMQPubSubListener{

    }

    class AbstractMessageParser{
        parse(bytes): Union[Start, Strop, Event]
    }

    AbstractListener <|-- ZMQListener
    ZMQListener <|-- ZMQPubSubListener
    AbstractListener o-- AbstractOperator
    AbstractListener o-- AbstractMessageParser

    AbstractPublisher <|-- ZMQPublisher
    ZMQPublisher <|-- ZMQPubSubPublisher


    AbstractOperator o-- AbstractPublisher
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
