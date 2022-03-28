// https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events
// This starts an SSE stream from http://localhost:8000/post-sse
const evtSource = new EventSource("post-sse")

// When a new event is received from the server, add a new item to the "ul" in the
// html we are running in.
evtSource.onmessage = function(event) {
    const newElement = document.createElement("li");
    const eventList = document.getElementById("mylist");
    const json_event = JSON.parse(event.data);
    console.log(json_event);
    newElement.innerHTML = eventAsHtml(json_event);
    newElement.id = json_event.object.metadata.uid;
    eventList.appendChild(newElement);
}

// On failure, just log it.
evtSource.onerror = function(err) {
  console.error("EventSource failed:", err);
};

// Create some pretty html for an event to be rendered in the browser.
function eventAsHtml(event) {
    const spec = event.object.spec
    var htmlcontent = `<b>${event.happened}</b><br/>`
    htmlcontent += `by <em>${spec.user}</em><br>`
    htmlcontent += `at <em>${event.object.metadata.creationTimestamp}</em><br/>`
    htmlcontent += `tagged: `
    spec.tags.forEach(function(item, index) {
        htmlcontent += `<span class="tags">${item} </span>`
    })
    
    htmlcontent += "<br/>"
    htmlcontent += `published: ${spec.published}<br/><pre>`
    htmlcontent += spec.content
    htmlcontent += "</pre><hr>"
    return htmlcontent
}
