document.addEventListener("DOMContentLoaded", () => {
    const quoteElement = document.getElementById("quote");
    
    // Only run quote logic if the element exists
    if (!quoteElement) {
        return; // Exit early if we're not on the home page
    }
    
    const quotes = [
        '"Habit is structure in your life."',
        '"Discipline builds freedom."',
        '"Small steps every day lead to big results."',
        '"Focus on consistency, not intensity."'
    ];

    const lastDate = localStorage.getItem("savedDate");
    const today = new Date().toLocaleDateString();

    if (today !== lastDate || !localStorage.getItem("quoteOfDay")) {
        const quote_of_day = date_changed(quotes);
        quoteElement.textContent = quote_of_day;
        localStorage.setItem("savedDate", today);
        localStorage.setItem("quoteOfDay", quote_of_day);
    } else {
        const savedQuote = localStorage.getItem("quoteOfDay");
        quoteElement.textContent = savedQuote;
    }

    function date_changed(quotes) {
        const randomIndex = Math.floor(Math.random() * quotes.length);
        return quotes[randomIndex];
    }
});
