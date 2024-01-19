# Edge to Cloud File Uploader


## MQTT API
The *Edge to Cloud File Uploader* exposes an MQTT API that allows one to control the device remotely, in particular, to trigger essential functions like mounting a memory card, browsing the file system, and issuing an upload job.
A client can trigger these functions by issuing command messages over dedicated command topics the *Edge to Cloud File Uploader* subscribes to. The *Edge to Cloud File Uploader* executes the respective function and publishes the result over a dedicated response topic the clients can subscribe to.

The *Edge to Cloud File Uploader* subscribes to several command topics with the format `cmd/[NAME]`, each addressing one or multiple functions, e.g., `cmd/jobs`, being associated with jobs-related functions. For each command topic, there exists a response topic with the format `stat/[NAME]`, e.g., `stat/jobs`.
If a command topic addresses multiple functions, the client has to specify the exact function over an additional `command` property in the message's payload (see details below). Moreover, the client may specify a `correlationId` in the payload of the command message. The *Edge to Cloud File Uploader* embeds this `correlationId` into the response message so that the client is able to correlate both messages (see details below). 

During device registration, it is possible to overwrite several topics, i.e., change the default topic names and structures at runtime. Note that this feature is not supported for all topics (see details below).

### State Topic
* Default topic: `stat`
* Can be overwritten: no
* Description: Every two seconds, the *Edge to Cloud File Uploader* publishes its current state over this topic. Note that this is the only topic that does not have a command counterpart topic, which means that responses are automatically generated and published without any command being issued.
* Response message payload:
```
{
  "isRegistered": false
}
```

### Query Topics
* Default command topic: `cmd/topics`
* Default response topic: `stat/topics`
* Can be overwritten: no
* Description: If a command message is set to this command topic, the *Edge to Cloud File Uploader* publishes a list of all active topics over the response topic.
* Command message payload:
```
{
  "correlationId": "query-topics-0"
}
```
* Response message payload:
```
{
  "topics": [
    {
      "topic": "stat",
      "relation": "responseStateTopic"
    },
    {
      "topic": "stat/topics",
      "relation": "responseTopicsTopic"
    },
    {
      "topic": "cmd/topics",
      "relation": "requestTopicsTopic"
    },
    {
      "topic": "cmd/sys",
      "relation": "requestSystemTopic"
    },
    {
      "topic": "stat/sys",
      "relation": "responseSystemTopic"
    },
    {
      "topic": "stat/register",
      "relation": "responseRegisterTopic"
    },
    {
      "topic": "cmd/register",
      "relation": "requestRegisterTopic"
    }
  ],
  "correlationId": "query-topics-0"
}
```





 




