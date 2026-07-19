
//Getting elements
const textarea = document.getElementById('textbox');            //User input textbox
const submitButton = document.getElementById('submit-button');  // Submit button
const output = document.getElementById('output');               // Output Testing

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




