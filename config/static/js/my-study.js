const overlay = document.getElementById("summary-overlay");
const content = document.getElementById("summary-content");

function viewSummary(id){

    //console.log(button.dataset.summary);
    const summary = summariesDict[id];

    content.innerHTML = "";

    // Title
    const title = document.createElement("h2");
    title.textContent = summary.title;
    content.appendChild(title);

    // Topics
    summary.topics.forEach(topic => {

        const heading = document.createElement("h3");
        heading.textContent = topic.heading;

        content.appendChild(heading);

        const list = document.createElement("ul");

        topic.points.forEach(point => {

            const item = document.createElement("li");
            item.textContent = point;

            list.appendChild(item);

        });

        content.appendChild(list);

    });

    // Key Takeaways
    const takeawaysHeading = document.createElement("h3");
    takeawaysHeading.textContent = "Key Takeaways";

    content.appendChild(takeawaysHeading);

    const takeawayList = document.createElement("ul");

    summary.key_takeaways.forEach(point => {

        const item = document.createElement("li");
        item.textContent = point;

        takeawayList.appendChild(item);

    });

    content.appendChild(takeawayList);

    overlay.classList.add("show");

}

function hideSummary(){
    overlay.classList.remove("show")
    
    content.replaceChildren()
}
