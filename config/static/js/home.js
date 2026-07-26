
//Getting elements
const textarea = document.getElementById('textbox');            //User input textbox
const submitButton = document.getElementById('submit-button');  // Submit button
const output = document.getElementById('response-content');               // Output Testing

// Automatic resizer for user input textbox
textarea.addEventListener("input", function() {
    textarea.style.height = "auto";                         // reset height
    textarea.style.height = textarea.scrollHeight + 'px';   // set new height
});

// Displaying output 
/*
    THIS IS TEMPORARY
    JUST TO CAPTURE USER INPUT AND DISPLAY IT BACK
*/
submitButton.addEventListener("click", function() {
    const userInput = textarea.value;   // get user input
    output.textContent = userInput;     // set TEST OUTPUT as content
    console.log(userInput);             // output also to console
    textarea.value = "";                // reset textarea
    textarea.style.height = "auto";     // reset height size

});


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


// Selecting active for study modes
const buttons = document.querySelectorAll(".mode");
const action = buttons[0].dataset.action;

buttons.forEach(button => {
    button.addEventListener("click", () => {
        // Remove active from all buttons
        buttons.forEach(btn => btn.classList.remove("active"));

        // Add active to clicked button
        button.classList.add("active");

        const action = button.dataset.action;
        
    });
});