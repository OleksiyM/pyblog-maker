document.addEventListener('DOMContentLoaded', function() {
    // Dark/Light Theme Toggle
    const themeToggle = document.getElementById('theme-toggle');

    if (themeToggle) { // Check if the button exists

        // Function to set theme
        function setTheme(themeName) {
            localStorage.setItem('theme', themeName);
            document.body.className = themeName; // Use class for styling
        }

        // Check for system theme preference
        function checkSystemTheme() {
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                setTheme('dark-theme');
            } else {
                setTheme('light-theme');
            }
        }
        // Check for saved theme or system theme
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
             setTheme(savedTheme);  //  Apply saved theme
        } else {
            checkSystemTheme();   // Apply System Theme
        }

        //  Toggle Theme
        themeToggle.addEventListener('click', () => {
            if (document.body.classList.contains('dark-theme')) {
                setTheme('light-theme');
            } else {
                setTheme('dark-theme');
            }
        });

         //  Listen for system theme changes.
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            const newColorScheme = e.matches ? "dark" : "light";
            setTheme(newColorScheme + "-theme");  // set "dark-theme" or "light-theme"
        });

    } // End of themeToggle check
});