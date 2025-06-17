// Wait for form to be submitted

document.getElementById("rsvpForm").addEventListener("submit", async function (e) {
    e.preventDefault(); // prevents page from reloading when form is submitted

    const form = e.target; //Get the form element

    // Create a JavaScript object with the form data

    const data = {
    name: form.name.value,         // Value from the "name" input
    email: form.email.value,       // Value from the "email" input
    hofstraId: form.hofstraId.value, // Value from the "hofstraId" input
    status: form.status.value,     // Value from the dropdown (student/guest)
    dietary: form.dietary.value    // Value from the dietary input
  };

  console.log("Form submitted:", data); // Print the data to the browser console for testing

  // TEMP: Simulate a successful submission by showing the message
  document.getElementById("message").classList.remove("hidden"); // Unhide the "submitted successfully" message
  form.reset(); // Clear the form after submission

});