const overlay = document.getElementById("summary-overlay");
const content = document.getElementById("summary-content");

function viewSummary(id){

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

function hidePopupContent(){
    overlay.classList.remove("show")
    
    content.replaceChildren()
}

function viewFlashcards(id){

    const flashcardData = flashcardsDict[id]
    const flashcards = flashcardData.flashcards;

    const content = document.getElementById("summary-content");

    content.innerHTML = "";


    const title = document.createElement("h2");
    title.textContent = flashcardData.title;

    content.appendChild(title);



    flashcards.forEach((card,index)=>{

        const flashcard = document.createElement("div");

        flashcard.className = "flashcard";


        flashcard.innerHTML = `

            <h3>
                Flashcard ${index + 1}
            </h3>


            <p>
                <strong>Question</strong>
            </p>

            <p>
                ${card.question}
            </p>


            <button class="show-answer-btn">
                Show Answer
            </button>


            <div class="answer" style="display:none;">

                <hr>

                <p>
                    <strong>Answer</strong>
                </p>

                <p>
                    ${card.answer}
                </p>

            </div>

        `;


        const button =
            flashcard.querySelector(".show-answer-btn");


        const answer =
            flashcard.querySelector(".answer");



        button.addEventListener("click",()=>{


            if(answer.style.display === "none"){

                answer.style.display = "block";
                button.textContent = "Hide Answer";

            }

            else{

                answer.style.display = "none";
                button.textContent = "Show Answer";

            }


        });


        content.appendChild(flashcard);


    });


    overlay.classList.add("show");

}
