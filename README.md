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
        operator: AbstractEventOperator

        start(): None  
        stop(): None
    }


    class AbstractEventOperator{
        publisher: AbstractPublisher
        start(Start): None
        stop(Start): None
        event(Event): None
    }

    class AbstractPublisher{
        publish(): None
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

    AbstractListener <|-- ZMQListener
    ZMQListener <|-- ZMQPubSubListener
    AbstractListener o-- AbstractEventOperator


    AbstractPublisher <|-- ZMQPublisher
    ZMQPublisher <|-- ZMQPubSubPublisher


    AbstractEventOperator o-- AbstractPublisher

    

```
