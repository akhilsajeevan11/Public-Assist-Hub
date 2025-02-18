// Example security improvements:
function previewImage(event) {
  const file = event.target.files[0];
  if (file && file.type.startsWith("image/")) {
    const reader = new FileReader();
    reader.onload = function () {
      const output = document.getElementById("preview");
      output.src = reader.result;
      output.style.display = "block";
      document.getElementById("viewImageBtn").style.display = "inline";
    };
    reader.readAsDataURL(file);
  } else {
    alert("Please upload a valid image file.");
  }
}

function viewImage() {
  const imgSrc = document.getElementById("preview").src;
  if (imgSrc) {
    window.open(imgSrc, "_blank");
  }
}

// Map and Location Autocomplete
let map, marker, autocomplete;

function initMap() {
  const defaultLocation = { lat: -34.397, lng: 150.644 };
  map = new google.maps.Map(document.getElementById("map"), {
    center: defaultLocation,
    zoom: 15,
  });

  marker = new google.maps.Marker({
    position: defaultLocation,
    map: map,
    title: "Selected Location",
  });

  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const userLocation = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        };
        map.setCenter(userLocation);
        marker.setPosition(userLocation);
        getPlaceName(userLocation.lat, userLocation.lng);
      },
      () => {
        alert(
          "Geolocation permission denied or not supported. Using default location."
        );
        map.setCenter(defaultLocation);
        marker.setPosition(defaultLocation);
        getPlaceName(defaultLocation.lat, defaultLocation.lng);
      }
    );
  }

  autocomplete = new google.maps.places.Autocomplete(
    document.getElementById("issueLocation")
  );
  autocomplete.addListener("place_changed", function () {
    let place = autocomplete.getPlace();
    if (!place.geometry) {
      alert("No details available for the selected location.");
      return;
    }
    map.setCenter(place.geometry.location);
    marker.setPosition(place.geometry.location);
  });
}

function getPlaceName(lat, lng) {
  let geocoder = new google.maps.Geocoder();
  let latlng = { lat: parseFloat(lat), lng: parseFloat(lng) };

  geocoder.geocode({ location: latlng }, function (results, status) {
    if (status === "OK") {
      if (results[0]) {
        document.getElementById("issueLocation").value =
          results[0].formatted_address;
      } else {
        alert("No address found for this location.");
      }
    } else {
      alert("Geocoder failed due to: " + status);
    }
  });
}

// Handle form submission with AJAX (CSRF, image upload, etc.)
document
  .getElementById("issueForm")
  .addEventListener("submit", function (event) {
    event.preventDefault();

    const title = document.getElementById("issueTitle").value;
    const description = document.getElementById("issueDescription").value;
    const location = document.getElementById("issueLocation").value;
    const image = document.getElementById("issueImage").files[0];

    // Basic validation
    if (!title || !description || !location) {
      alert("Please fill out all required fields.");
      return;
    }

    const formData = new FormData();
    formData.append("title", title);
    formData.append("description", description);
    formData.append("location", location);
    if (image) {
      formData.append("image", image);
    }

    fetch("/submit_issue", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        alert(data.message);
        loadIssues();
      })
      .catch((error) => {
        alert("Error submitting issue: " + error);
      });
  });

// Load issues for tracking and feedback
function loadIssues() {
  fetch("/get_issues")
    .then((response) => response.json())
    .then((issues) => {
      const table = document.getElementById("issuesTable");
      table.innerHTML = "";
      issues.forEach((issue) => {
        const badgeColor =
          issue.status === "Resolved"
            ? "bg-success"
            : issue.status === "In Progress"
            ? "bg-warning"
            : "bg-danger";
        table.innerHTML += `
          <tr>
            <td>${issue.title}</td>
            <td><span class="badge ${badgeColor}">${issue.status}</span></td>
            <td>
              <button class="btn btn-sm btn-info" onclick="showFeedbackForm(${issue.id})">
                <i class="fas fa-comment"></i> Feedback
              </button>
            </td>
          </tr>
        `;
      });
    });
}

// Initialize issues on page load
document.addEventListener("DOMContentLoaded", loadIssues);
