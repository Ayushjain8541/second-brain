# AWS learnings

> Source: Notion page "AWS learnings" — https://app.notion.com/p/379ef141e35780a88879da03b920de27
> Exported: 2026-06-19

### Lambda
Run some function and then only pay for the compute of that function. Lambda will spin up some processor to run your function (based on the language), execute it, then go back to sleep
AWS handles all of the load balancing, scaling etc to cater to very high thoroughput. (event-driven)

### Amazon API gateway
In between the user and ur microservices. Handles auth and security, rate limiting and routing to which micro service needs to be used. (decouple middleware and router from backend routing) (see backend learnings)

### S3
Massive data lake (data dump) to store all your big files and everything

### EC2
Persistent server for you to consistently have a server up and running for functions and to receive stuff (webhooks) as well.

### Auroroa DLB
Fully managed system for database (postgres)

### SQS
Event broker - it handles the buffering to your microservices. Instead of sending all 10000 requests at once to your microservices, it will use a queue to buffer and send to the microservice as much as it can manage
- Workers (lambdas) are spinned up and take from the queue whenever they can)

### Eventbridge
Event broker - it handles the routing to your microservices. When a call is made, which microservice needs to be triggered

### Temporal
Temporal is like a way to break some very long function into different "save states" that you can refresh and go back to at any time. And if the function fails at some part and then it restarts, it will go back to that save state rather than starting from the start.
