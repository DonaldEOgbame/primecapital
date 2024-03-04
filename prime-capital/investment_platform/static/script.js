document.getElementById('verification-form').addEventListener('submit', function (event) {
  event.preventDefault();
  var formData = new FormData(event.target);
  var action = formData.get('action');

  if (action === 'verify') {
    // Handle verification code submission
    fetch("/email-verify/", {
      method: "POST",
      headers: {
        "X-CSRFToken": formData.get('csrfmiddlewaretoken'),
      },
      body: formData,
    })
      .then(response => response.json())
      .then(data => {
        alert(data.message); // Show success or error message for verification action
        // You may want to redirect here on success
      })
      .catch(error => {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
      });
  } else if (action === 'resend') {
    // Handle resend verification code
    var email = formData.get('email');
    resendVerificationCode(email);
  }
});

function resendVerificationCode(email) {
  fetch("/api/resend-verification-code/", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-CSRFToken": getCSRFToken(),
    },
    body: "email=" + encodeURIComponent(email),
  })
    .then(response => response.json())
    .then(data => {
      alert(data.message); // Show success or error message for resend action
      // You may want to handle the response accordingly
    })
    .catch(error => {
      console.error("Error:", error);
      alert('An error occurred. Please try again.');
    });
}
