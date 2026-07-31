console.log("reached print")

// Profile Picture and Dropdown menu
const profilePic = document.getElementById("profile-pic");
const dropdown = document.getElementById("profile-dropdown");

profilePic.addEventListener("click", (e) => {
    e.stopPropagation();
    dropdown.classList.toggle("show");
});

document.addEventListener("click", () => {
    dropdown.classList.remove("show");
});


// Automatic Resizer for User Input Textbox
const textarea = document.getElementById("textbox");
const submitButton = document.getElementById("submit-button");

textarea.addEventListener("input", function () {
    textarea.style.height = "auto";
    textarea.style.height = textarea.scrollHeight + "px";
});


// Selecting active study mode
const buttons = document.querySelectorAll(".mode");
let action = buttons[0].dataset.action;

buttons.forEach(button => {
    button.addEventListener("click", () => {

        buttons.forEach(btn => btn.classList.remove("active"));

        button.classList.add("active");

        action = button.dataset.action;
    });
});


// Output area
const output = document.getElementById("response-content");


// Submit user input to Gemini
submitButton.addEventListener("click", async function () {

    const userInput = textarea.value.trim();

    if (!userInput) {
        output.textContent = "Please enter some notes first.";
        return;
    }

    output.textContent = "Please wait while we are generating your study material...";

    let endpoint = `/api/study-tools/${action}/`;
    let bigBody = {text: userInput};

    // Special case for quiz
    if (action === "quiz") {

        console.log("shouldnt see me")
        
        endpoint = "/api/quiz/generate";
        bigBody = {
            notes: userInput,
            num_questions: 5
        
        }

    }

    try {

        console.log("reached 2")
        
        const response = await fetch (
            endpoint,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRF("csrftoken")
                },
                body: JSON.stringify(bigBody)
            }
            
        );

        console.log("reached 3")

        const data = await response.json();


        if (!response.ok) {
            throw new Error(data.error || "Something went wrong.");
        }

        if (action === "summary") {

            console.log("reached 4")
            console.log(data);

            displaySummary(data);

            console.log("reached 7")

        }

        else if (action === "flashcards") {

            console.log("reached flashcards?")

            displayFlashcards(data.flashcards);

        }
        else if (action === "quiz") {

            window.location.href = `/quiz/?quiz_id=${data.quiz_id}`;
        }

    }
    catch (error) {

        output.textContent = `There was an error making your ${action}:`;
        console.log("Error:", error)

    }

    textarea.value = "";
    textarea.style.height = "auto";

});


// Get Django CSRF Token
function getCSRF(name) {

    let cookieVal = null;

    if (document.cookie && document.cookie !== "") {

        const cookies = document.cookie.split(";");

        for (let cookie of cookies) {

            cookie = cookie.trim();

            if (cookie.startsWith(name + "=")) {

                cookieVal = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }

    return cookieVal;
}


// Display Flashcards
function displayFlashcards(flashcards) {

    output.innerHTML = "";

    flashcards.forEach((card, index) => {

        const flashcard = document.createElement("div");
        flashcard.className = "flashcard";

        flashcard.innerHTML = `
            <h3>Flashcard ${index + 1}</h3>

            <p><strong>Question</strong></p>
            <p>${card.question}</p>

            <button class="show-answer-btn">
                Show Answer
            </button>

            <div class="answer" style="display:none;">
                <hr>
                <p><strong>Answer</strong></p>
                <p>${card.answer}</p>
            </div>
        `;

        const button = flashcard.querySelector(".show-answer-btn");
        const answer = flashcard.querySelector(".answer");

        button.addEventListener("click", () => {

            if (answer.style.display === "none") {

                answer.style.display = "block";
                button.textContent = "Hide Answer";

            } else {

                answer.style.display = "none";
                button.textContent = "Show Answer";

            }

        });

        output.appendChild(flashcard);

    });

}


// Display Summary
function displaySummary(summary) {

    console.log("reached 5")
    output.innerHTML = "";

    const title = document.createElement("h2");
    title.textContent = summary.title;
    output.appendChild(title);

    summary.topics.forEach(topic => {

        const heading = document.createElement("h3");
        heading.textContent = topic.heading;

        output.appendChild(heading);

        const list = document.createElement("ul");

        topic.points.forEach(point => {

            const item = document.createElement("li");
            item.textContent = point;
            list.appendChild(item);

        });

        output.appendChild(list);

    });

    const takeawaysHeading = document.createElement("h3");
    takeawaysHeading.textContent = "Key Takeaways";
    output.appendChild(takeawaysHeading);

    const takeawayList = document.createElement("ul");

    summary.key_takeaways.forEach(point => {

        const item = document.createElement("li");
        item.textContent = point;
        takeawayList.appendChild(item);

    });

    output.appendChild(takeawayList);

    console.log("reached 6")

}
