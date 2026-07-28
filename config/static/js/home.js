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
const textarea = document.getElementById('textbox');            //User input textbox
const submitButton = document.getElementById('submit-button');  // Submit button


textarea.addEventListener("input", function() {
    textarea.style.height = "auto";                         // reset height
    textarea.style.height = textarea.scrollHeight + 'px';   // set new height
});


// Selecting active for study modes
const buttons = document.querySelectorAll(".mode");
let action = buttons[0].dataset.action;

buttons.forEach(button => {
    button.addEventListener("click", () => {
        // Remove active from all buttons
        buttons.forEach(btn => btn.classList.remove("active"));

        // Add active to clicked button
        button.classList.add("active");

        // Set selected action
        action = button.dataset.action;
        
    });
});


// Submit user input to Gemini API Call
const output = document.getElementById('response-content');

submitButton.addEventListener("click", async function() {
    const userInput = textarea.value.trim();   // get user input
    
    if (!userInput) {
        output.textContent = "Please enter some notes first.";
        return;
    }

    output.textContent = "Please wait while we are generating your study material...";
    console.log(`/api/study-tools/${action}/`);
    try {
        
        const response = await fetch (
            `/api/study-tools/${action}/`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRF("csrftoken")
                },
                body: JSON.stringify({text: userInput})
            }
            
        );

        const data = await response.json();

        if (!response.ok) {

            throw new Error(data.error || "something went wrong.");
        }

        // Finally Displaying Output

        if (action === "summarize") {

            output.textContent = displaySummary(data.summary);
        }

        else if (action === "flashcards") {

            output.textContent = data.flashcards;
        }

        else if (action === "quiz") {

            output.textContent = data.quiz;
        }

    }

    catch(error) {

        console.log(error)

        output.textContent = "Error: " + error.message;
    }



    // Reset box back
    textarea.value = "";
    textarea.style.height = "auto";
});


// Get Django CSRF Token
function getCSRF(name) {
    
    let cookieVal = null;

    if (document.cookie && document.cookie !== "") {

        const cookies = document.cookie.split(";")
    

        for (let cookie of cookies) {

            cookie = cookie.trim();

            if (cookie.startsWith(name+"=")) {

                cookieVal = decodeURIComponent(cookie.substring(name.length+1));
                break;
            }
        }
    
    }

    return cookieVal;
}

// Display Quiz Nicely
function displayQuiz(quiz) {

    output.innerHTML = "";


    quiz.forEach((item, index) => {

        const question = document.createElement("div");


        question.innerHTML = `
            <h3>${index + 1}. ${item.question}</h3>

            <ul>
                ${item.choices.map(choice =>
                    `<li>${choice}</li>`
                ).join("")}
            </ul>

            <p><strong>Answer:</strong> ${item.answer}</p>
            <hr>
        `;


        output.appendChild(question);

    });

}

// Display Summary Nicely
function displaySummary(summary) {
    output.innerHTML = "";

    // Title Section
    const title = document.createElement("h2");
    title.textContent = summary.title;
    output.appendChild(title);

    // Topics Section
    summary.topics.forEach(topic => {

        const heading = document.createElement("h3");
        heading.textContent = topic.heading;
        output.appendChild(heading);

        const list = document.createElement("ul");

        topic.points.forEach(point => {

            const item = document.createElement("li");
            item.textContent = point
            list.appendChild(item);

        })

        output.appendChild(list);
    })

    // Key Takeaways Section
    const takeawaysHeading = document.createElement("h3");
    takeawaysHeading.textContent = "Key Takeaways";
    output.appendChild(takeawaysHeading);

    const takeawayList = document.createElement("ul");
    summary.key_takeaways.forEach(point => {

        const item = document.createElement("li");
        item.textContent = point;
        takeawayList.appendChild(item);
    })

    output.appendChild(takeawayList)
}