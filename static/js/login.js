document.addEventListener("DOMContentLoaded", function () {
  const sendOtpBtn = document.getElementById("sendOtpBtn");
  const verifyOtpBtn = document.getElementById("verifyOtpBtn");
  const otpRequestForm = document.getElementById("otpRequestForm");
  const otpVerifyForm = document.getElementById("otpVerifyForm");
  const emailInput = document.getElementById("email");
  const otpInput = document.getElementById("otp");

  // Backend API Base URL
  const API_BASE_URL = "http://127.0.0.1:5000";

  // Add these validation functions
  const isValidEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const isValidOTP = (otp) => /^\d{6}$/.test(otp);

  // Modified Send OTP handler
  sendOtpBtn.addEventListener("click", async function () {
    const email = emailInput.value.trim();
    
    if (!isValidEmail(email)) {
      alert("Please enter a valid email address (e.g., user@example.com)");
      return;
    }

    try {
      const response = await fetch(`/login`, {  // Changed to match your Flask route
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to send OTP');
      }

      // Your existing UI updates
      alert(data.message);
      otpRequestForm.style.display = "none";
      otpVerifyForm.style.display = "block";
      otpInput.focus();  // Added focus to OTP field

    } catch (error) {
      console.error("Error:", error);
      alert(error.message);
    }
  });

  // Enhanced Verify OTP handler
  verifyOtpBtn.addEventListener("click", async function () {
    const otp = otpInput.value.trim();
    const email = emailInput.value.trim();

    if (!isValidOTP(otp)) {
      alert("Please enter a 6-digit numeric OTP");
      return;
    }

    try {
      const response = await fetch(`/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, otp }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'OTP verification failed');
      }

      // Your existing success handling
      alert(data.message);
      window.location.href = "/home";

    } catch (error) {
      console.error("Error:", error);
      alert(error.message);
      otpInput.value = "";  // Clear invalid OTP
      otpInput.focus();
    }
  });
});
