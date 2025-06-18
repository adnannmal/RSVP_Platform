// unhide guest when guest is selected

document.addEventListener("DOMContentLoaded", function () {
  const statusSelect = document.getElementById("statusSelect");
  const guestField = document.getElementById("guestField");

  const guest1fname = document.querySelector('input[name="guest1fname"]');
  const guest1lname = document.querySelector('input[name="guest1lname"]');
  const guest2fname = document.querySelector('input[name="guest2fname"]');
  const guest2lname = document.querySelector('input[name="guest2lname"]');

  statusSelect.addEventListener("change", function () {
    const selected = this.value;

    const showGuests = selected === "guest";
    guestField.classList.toggle("hidden", !showGuets);

    guest1fname.required = showGuests;
    guest1lname.required = showGuests;
    //guest is optional
    guest2fname.required = false;
    guest2lname.required = false;

  });


  // Wait for form to be submitted

  document.getElementById("rsvpForm").addEventListener("submit", function (e) {
    e.preventDefault(); // prevents page from reloading when form is submitted

    const form = e.target; //Get the form element
    const email = form.email.value.trim();
    const emailPattern = /^[a-zA-Z0-9._%+-]+@pride\.hofstra\.edu$/;

    //check if email format is correct
    if (!emailPattern.test(email)) {
      alert("Please enter a valid pride email address")
      return;
    }

    // Create object with the form data

    const data = {
      fname: form.fname?.value,
      lname: form.lname?.value,
      hofstraId: form.hofstraId?.value,
      email: email,
      status: form.status.value,
      guest1fname: guest1fname.value,
      guest1lname: guest1lname.value,
      guest2fname: guest2fname.value,
      guest2lname: guest2lname.value,
    };


  console.log("Form submitted:", data); // Print the data to the browser console for testing

  // Simulate a successful submission by showing the message
  document.getElementById("message").classList.remove("hidden"); // Unhide the "submitted successfully" message

  form.reset(); // Clear the form after submission

  });
});