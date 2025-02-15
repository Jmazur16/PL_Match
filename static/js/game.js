document.addEventListener('DOMContentLoaded', () => {
    const playerHeadshot = document.getElementById('playerHeadshot');
    const lastNameInput = document.getElementById('lastName');
    const teamInput = document.getElementById('team');
    const submitButton = document.getElementById('submitGuess');
    const nextButton = document.getElementById('nextPlayer');
    const resultDiv = document.getElementById('result');

    // Get sport type from the window object (set in template)
    const sportType = window.SPORT_TYPE || 'nfl';

    // Function to crop image using canvas and convert to black and white
    function cropAndDisplayImage(imageUrl) {
        const img = new Image();
        img.crossOrigin = "anonymous";  // Enable CORS
        
        img.onload = function() {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            // Calculate crop dimensions
            // Width: crop 35% from each side (leaving 30% of original width)
            const cropWidth = img.width * 0.3;  
            const startX = img.width * 0.35;  // Start 35% from left
            
            // Height: keep full top, crop 35% from bottom
            const cropHeight = img.height * 0.65;  // Keep 65% of height
            const startY = 0;  // Start from top
            
            // Set canvas size to cropped dimensions
            canvas.width = cropWidth;
            canvas.height = cropHeight;
            
            // Draw cropped portion of image to canvas
            ctx.drawImage(img,
                startX, startY, cropWidth, cropHeight,  // Source rectangle
                0, 0, cropWidth, cropHeight  // Destination rectangle
            );
            
            // Get the image data to manipulate pixels
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;
            
            // Convert to black and white by averaging RGB values
            for (let i = 0; i < data.length; i += 4) {
                const avg = (data[i] + data[i + 1] + data[i + 2]) / 3;
                data[i] = avg;     // Red
                data[i + 1] = avg; // Green
                data[i + 2] = avg; // Blue
                // data[i + 3] is alpha (transparency), we don't need to change it
            }
            
            // Put the modified image data back on the canvas
            ctx.putImageData(imageData, 0, 0);
            
            // Update the image source with cropped and B&W version
            playerHeadshot.src = canvas.toDataURL();
        };
        
        img.onerror = function() {
            console.error('Error loading image for cropping');
            playerHeadshot.src = imageUrl;  // Fallback to original image
        };
        
        img.src = imageUrl;
    }

    // Load initial player
    loadNewPlayer();

    function loadNewPlayer() {
        fetch(`/get_player?sport=${sportType}`)
            .then(response => response.json())
            .then(data => {
                // Instead of setting src directly, crop first
                cropAndDisplayImage(data.headshot_url);
            })
            .catch(error => {
                console.error('Error loading player:', error);
                resultDiv.innerHTML = 'Error loading player. Please try again.';
                resultDiv.className = 'result-container incorrect';
            });
    }

    submitButton.addEventListener('click', checkAnswer);
    nextButton.addEventListener('click', () => {
        // Reset the game state
        lastNameInput.value = '';
        teamInput.value = '';
        resultDiv.innerHTML = '';
        resultDiv.className = 'result-container';
        submitButton.style.display = 'block';
        nextButton.style.display = 'none';
        
        // Load new player
        loadNewPlayer();
    });

    // Allow Enter key to submit
    [lastNameInput, teamInput].forEach(input => {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                if (nextButton.style.display === 'none') {
                    checkAnswer();
                } else {
                    nextButton.click();
                }
            }
        });
    });

    function checkAnswer() {
        const lastName = lastNameInput.value.trim();
        const team = teamInput.value.trim();

        if (!lastName || !team) {
            resultDiv.innerHTML = 'Please enter both a last name and a team.';
            resultDiv.className = 'result-container incorrect';
            return;
        }

        fetch('/check_answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                lastName: lastName,
                team: team
            })
        })
        .then(response => response.json())
        .then(data => {
            let resultMessage = '';
            
            if (data.nameCorrect && data.teamCorrect) {
                resultMessage = `Correct! That's ${data.correctName} of the ${data.correctTeam}!`;
                resultDiv.className = 'result-container correct';
            } else {
                resultMessage = `Incorrect. The correct answer was ${data.correctName} of the ${data.correctTeam}.`;
                resultDiv.className = 'result-container incorrect';
            }
            
            resultDiv.innerHTML = resultMessage;
            submitButton.style.display = 'none';
            nextButton.style.display = 'block';
        })
        .catch(error => {
            console.error('Error checking answer:', error);
            resultDiv.innerHTML = 'Error checking answer. Please try again.';
            resultDiv.className = 'result-container incorrect';
        });
    }
}); 