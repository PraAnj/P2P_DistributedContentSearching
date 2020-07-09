##### How to run java bootstrap server

1. Go to src/BootstrapServer/java
2. javac BootstrapServer.java
3. java BootstrapServer

##### How to connect from python node

1. Go to src
2. Run the python script as below.

> "cd src "    
> "python pythonNode.py <ip\_bs> <port\_bs> <ip\_self> <port\_self> <name\_self>"    
> ex: python pythonNode.py 192.168.1.2 55555 127.0.0.1 8081 node1     

##### To Exit from the network 

1. Give X as the input to exit the network

> "cd src "    
> "python pythonNode.py <ip\_bs> <port\_bs> <ip\_self> <port\_self> <name\_self>"    
> ex: python pythonNode.py 192.168.1.2 55555 127.0.0.1 8081 node1     


##### [Design doc link](https://docs.google.com/document/d/1uFmo2mkXFP7MTKHK0JH8DNljEBTw6HCyzuFfGKkhdEM/edit)

| Item (with error handling) | Status | Assignee |
| -------------------------- | ------ | -------- |
| REG to BS | Done | Imalka |
| REGOK from BS |  | Imalka |
| JOIN to peers | Done | Imalka |
| JOINOK from peers |  | Imalka |
| UNREG to BS | Done | Ashirwada |
| UNROK from BS | Done | Ashirwada |
| LEAVE to peers | Done | Ashirwada |
| LEAVEOK from peers | Done | Ashirwada |
| SER to peers |  | Prageeth |
| SEROK from file holder |  | Prageeth |
| ERROR |  | All |
| Structuring the code |  | Finalize via a meeting at the end |
| README udpate (how compiles/ run) |  | All |
| Event loop (Switch case) for P2P network thread |  | All |
| Draw state machine (Report) |  | All |
| Timeouts for responses |  | All |
| File downloader thread | Phase 3 |  |
| File downloader REST API | Phase 3 |  |
| Performance matric | Phase 4 |  |