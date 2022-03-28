// https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events
// This starts an SSE stream from http://localhost:8000/post-sse
const evtSource = new EventSource("post-sse")

// When a new event is received from the server, add a new item to the "ul" in the
// html we are running in.
evtSource.onmessage = function(event) {
    const eventList = document.getElementById("mylist");
    const json_event = JSON.parse(event.data);
    console.log(json_event);
    if (json_event.happened == "ADDED") {
        addPost(json_event, eventList)
    } else if (json_event.happened == "MODIFIED") {
        updatePost(json_event, eventList)
    }

}

// On failure, just log it.
evtSource.onerror = function(err) {
  console.error("EventSource failed:", err);
};

// addPost will add a new post to the current page. It currently
// doesn't do a sanity check if the Post already exists in the page.
function addPost(json_event, parent) {
    const el = document.getElementById(json_event.object.metadata.uid);
    if (el !== null) {
        // This implies that the post already exists and that this is a
        // duplicate event. In that case, just update the existing post
        // instead of having to add a new one.
        return updatePost(json_event);
    }
    // Looks like this post doesn't already exists, so create a new one.
    const newElement = document.createElement("li");
    newElement.innerHTML = eventAsHtml(json_event);
    newElement.id = json_event.object.metadata.uid;
    newElement.classList.add('post');
    parent.appendChild(newElement);
}

// update an existing post to the new content.
function updatePost(json_event) {
    const post = document.getElementById(json_event.object.metadata.uid);
    const html_content = eventAsHtml(json_event);
    const timeElapsed = Date.now();
    const today = new Date(timeElapsed);
    // Add the last update date to the post.
    const new_html = html_content + `<small>Updated at ${today.toISOString()}</small>`;
    change(post, new_html);
}

// Create some pretty html for an event to be rendered in the browser.
function eventAsHtml(event) {
    const spec = event.object.spec
    var htmlcontent = `by <em>${spec.user}</em><br>`
    htmlcontent += `at <em>${event.object.metadata.creationTimestamp}</em><br/>`
    htmlcontent += `tagged: `
    spec.tags.forEach(function(item, index) {
        htmlcontent += `<span class="tags">${item} </span>`
    })

    htmlcontent += "<br/>"
    htmlcontent += `published: ${spec.published}<br/><pre>`
    htmlcontent += spec.content
    htmlcontent += "</pre>"
    return htmlcontent
}

// Add some little animation when changing
function change(elem, new_html) {
    elem.classList.add('hide');
    elem.innerHTML = new_html;
    setInterval(function() {
        elem.classList.remove('hide');
    }, 500);
}
