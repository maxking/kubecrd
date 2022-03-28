const evtSource = new EventSource("post-sse")
evtSource.onmessage = function(event) {
    const newElement = document.createElement("li");
    const eventList = document.getElementById("mylist");
    const json_event = JSON.parse(event.data);
    console.log(json_event);
    newElement.innerHTML = eventAsHtml(json_event);
    newElement.id = json_event.object.metadata.uid;
    eventList.appendChild(newElement);
}

evtSource.onerror = function(err) {
  console.error("EventSource failed:", err);
};

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
