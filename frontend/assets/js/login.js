document.addEventListener("DOMContentLoaded", function () {
  const sendOtpBtn = document.getElementById("sendOtpBtn");
  const verifyOtpBtn = document.getElementById("verifyOtpBtn");
  const otpRequestForm = document.getElementById("otpRequestForm");
  const otpVerifyForm = document.getElementById("otpVerifyForm");
  const emailInput = document.getElementById("email");
  const otpInput = document.getElementById("otp");

  // Backend API Base URL
  const API_BASE_URL = "http://127.0.0.1:5000";

  // Send OTP Request
  sendOtpBtn.addEventListener("click", async function () {
    const email = emailInput.value.trim();
    if (!email) {
      alert("Please enter a valid email.");
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/request-otp`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();
      if (response.ok) {
        alert(data.message);
        otpRequestForm.style.display = "none"; // Hide email form
        otpVerifyForm.style.display = "block"; // Show OTP form
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (error) {
      console.error("Error sending OTP:", error);
      alert("Failed to send OTP. Please try again.");
    }
  });

  // Verify OTP
  verifyOtpBtn.addEventListener("click", async function () {
    const otp = otpInput.value.trim();
    if (!otp) {
      alert("Please enter the OTP.");
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/verify-otp`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email: emailInput.value, otp }),
      });

      const data = await response.json();
      if (response.ok) {
        alert(data.message);
        window.location.href = "/dashboard"; // Redirect after successful login
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (error) {
      console.error("Error verifying OTP:", error);
      alert("Failed to verify OTP. Please try again.");
    }
  });
});
