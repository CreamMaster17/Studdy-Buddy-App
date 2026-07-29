const quizData = window.djangoQuiz;
const quizId = window.quizId || new URLSearchParams(window.location.search).get("quiz_id");


if (!quizData) {

    document.body.innerHTML = 
        "<h2>No quiz found.</h2>";

    throw new Error("Missing quiz data");

}


const title = document.getElementById("quiz-title");
const container = document.getElementById("questions-container");


title.textContent = quizData.quiz_title;



quizData.questions.forEach(question => {


    const div = document.createElement("div");

    div.className = "question";


    div.innerHTML = `

        <h3>
            ${question.question_id}.
            ${question.question_text}
        </h3>

    `;


    Object.entries(question.options).forEach(([key,value]) => {


        div.innerHTML += `

            <label>

                <input 
                    type="radio"
                    name="${question.question_id}"
                    value="${key}"
                >

                ${key}. ${value}

            </label>

            <br>

        `;


    });


    container.appendChild(div);


});



document
.getElementById("quiz-form")
.addEventListener("submit", async function(event){


    event.preventDefault();


    const answers = {};


    document
    .querySelectorAll("input[type=radio]:checked")
    .forEach(input => {

        answers[input.name] = input.value;

    });

    const endpoint = quizId ? `/api/quiz/submit-and-save/${quizId}/` : "/api/quiz/submit-and-save/";

    const response = await fetch(
    endpoint,
    {
        method:"POST",

        headers:{
            "Content-Type":"application/json",
            "X-CSRFToken":getCSRF("csrftoken")
        },

        body:JSON.stringify({
            answers:answers
        })
    }
);


const data = await response.json();


document
.querySelectorAll(".question")
.forEach(question => {

    question.classList.remove(
        "correct",
        "incorrect"
    );

});



data.question_results.forEach(result => {

    const questionDiv = document
        .querySelector(
            `.question:nth-child(${result.question_id})`
        );


    if (!questionDiv) return;


    if (result.is_correct) {

        questionDiv.classList.add("correct");

    } else {

        questionDiv.classList.add("incorrect");

    }

});



document.getElementById("results").innerHTML = `

<h2>
Score: ${data.score_percentage}%
</h2>

<p>
${data.correct_count}/${data.total_questions}
correct
</p>

`;


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