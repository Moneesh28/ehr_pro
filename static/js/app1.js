<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blood Report Analyzer</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom"></script>
</head>
<body class="bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-200">
    
    <nav class="bg-white dark:bg-gray-800 shadow-md p-4 flex justify-between items-center fixed w-full top-0 z-50">
        <h1 class="text-3xl font-extrabold text-blue-600 dark:text-white">Blood Report Analyzer</h1>
        <div>
            <button id="darkModeToggle" class="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition">🌙 Dark Mode</button>
            <a href="/" class="ml-2 px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition">Home</a>
            <a href="/logout" class="ml-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition">Logout</a>
        </div>
    </nav>
    
    <div class="flex items-center justify-center min-h-screen pt-20">
        <div class="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-8 w-full max-w-3xl">
            <h2 class="text-3xl font-bold text-center text-blue-600 dark:text-white">Welcome, {{ username }}</h2>
            <p class="text-center text-gray-600 dark:text-gray-400 mt-2">Upload and analyze your blood reports seamlessly</p>
            
            <form id="uploadForm" class="mt-6 space-y-4">
                <label for="files" class="block text-gray-700 dark:text-gray-300 font-semibold">Upload PDF Reports:</label>
                <input type="file" id="files" name="files" multiple accept="application/pdf" class="w-full p-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                <button type="submit" class="w-full px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition">Analyze Reports</button>
            </form>
            
            <div id="loading" class="hidden text-center text-blue-600 font-bold mt-4">Processing...</div>
            
            <div id="output" class="mt-6 hidden">
                <canvas id="timeGraph" class="w-full h-80"></canvas>
                <h3 class="text-xl font-bold mt-6 text-gray-800 dark:text-white">Summarized Remarks:</h3>
                <div id="summaryContainer" class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4"></div>
            </div>
        </div>
    </div>
    
    <footer class="mt-16 text-center text-gray-600 dark:text-gray-400 py-8">
        <p>&copy; 2025 Blood Report Analyzer. All rights reserved.</p>
        <p>Privacy Policy | Terms of Service | Contact Us</p>
    </footer>
    
    <script>
        document.getElementById("uploadForm").addEventListener("submit", async function (e) {
            e.preventDefault();
            document.getElementById("loading").classList.remove("hidden");
            document.getElementById("output").classList.add("hidden");
            
            const files = document.getElementById("files").files;
            if (files.length === 0) {
                alert("Please upload at least one file.");
                return;
            }
            
            const formData = new FormData();
            for (const file of files) {
                formData.append("file", file);
            }
            
            try {
                const response = await fetch("/upload", { method: "POST", body: formData });
                if (!response.ok) throw new Error("Failed to analyze reports.");
                
                const result = await response.json();
                document.getElementById("loading").classList.add("hidden");
                document.getElementById("output").classList.remove("hidden");
                
                const labels = result.data.map(item => item.Date);
                const datasets = [
                    { label: "Hemoglobin (g/dL)", data: result.data.map(item => item.Hemoglobin), borderColor: "blue" },
                    { label: "RBC (million/µL)", data: result.data.map(item => item.RBC), borderColor: "red" },
                    { label: "WBC (thousand/µL)", data: result.data.map(item => item.WBC), borderColor: "green" },
                    { label: "Platelets (thousand/µL)", data: result.data.map(item => item.Platelets), borderColor: "orange" },
                    { label: "HCT (%)", data: result.data.map(item => item.HCT), borderColor: "purple" },
                ].map(dataset => ({ ...dataset, fill: false, borderWidth: 2, lineTension: 0.4, pointRadius: 4 }));
                
                new Chart(document.getElementById("timeGraph").getContext("2d"), {
                    type: "line",
                    data: { labels, datasets },
                    options: {
                        responsive: true,
                        plugins: { zoom: { zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: "x" } } },
                        scales: { x: { title: { display: true, text: "Date" } }, y: { title: { display: true, text: "Values" } } }
                    }
                });
                
                const summaryContainer = document.getElementById("summaryContainer");
                summaryContainer.innerHTML = result.remarks_summary.map(rem => `<div class='p-4 bg-gray-200 dark:bg-gray-700 rounded-lg'>${rem}</div>`).join('');
            } catch (error) {
                alert(error.message);
            }
        });
        
        document.getElementById("darkModeToggle").addEventListener("click", () => {
            document.body.classList.toggle("dark");
        });
    </script>
</body>
</html>
