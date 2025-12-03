<div align="center">
  
  <h1 style="font-size: 38px; font-weight: bold;">⚡ Python Automation Script With Data Processing + AI API Integration</h1>

  <p style="font-size: 18px;">
    A fully automated data pipeline that performs cleaning, transformation, visualization, AI insights, and PDF reporting.
  </p>

  <!-- IMAGE SLOTS – Replace with your images -->
  <img 
  src="https://github.com/user-attachments/assets/ffb1856d-ab4d-4de8-88ad-544c1c07f78e" 
  alt="Project Preview 1" 
  width="47%" 
  style="margin-right: 10px; border-radius: 10px;"
>

<img 
  src="https://github.com/user-attachments/assets/11aea522-0e9b-41be-b4a0-be2ffc971952" 
  alt="Project Preview 2" 
  width="47%" 
  style="border-radius: 10px;"
>

  <br><br>
</div>

<hr>

<h2>🚀 Overview</h2>

<p>
This project is a powerful <strong>Python automation tool</strong> designed to handle dataset cleaning, transformation, visualization, AI analysis, and PDF report generation.
It supports <strong>CSV, Excel, and JSON</strong> formats and uses <strong>Gemini AI</strong> by default for automated insights.
</p>

<ul>
  <li>Auto detects file type</li>
  <li>Cleans & transforms dataset</li>
  <li>Generates AI insights (Gemini / OpenAI / HuggingFace compatible)</li>
  <li>Creates bar chart visualizations</li>
  <li>Exports a full PDF report</li>
  <li>Comes with both CLI menu & auto mode</li>
</ul>

<hr>

<h2>📁 Project Structure</h2>

<pre>
project/
├── data_ai_automator.py
├── requirements.txt
├── .env
├── README.md
└── sample.csv
</pre>

<hr>

<h2>🧪 Dataset Info</h2>

<p>The sample dataset contains:</p>

<ul>
  <li>order_id</li>
  <li>date</li>
  <li>customer_name</li>
  <li>product</li>
  <li>category</li>
  <li>price</li>
  <li>quantity</li>
  <li>city</li>
</ul>

<p>Works with any CSV / Excel / JSON table format.</p>

<hr>

<h2>🧼 Data Cleaning (PART A)</h2>

<p>The cleaning pipeline performs the following:</p>

<ul>
  <li>Remove duplicates</li>
  <li>Handle missing values (median for numeric, mode for text)</li>
  <li>Standardize date formats</li>
  <li>Convert numeric-like text into numbers</li>
  <li>Remove invalid negative rows</li>
  <li>Convert column names to snake_case</li>
</ul>

<p>A ProcessingSummary tracks:</p>

<ul>
  <li>Rows before cleaning</li>
  <li>Rows after cleaning</li>
  <li>Duplicates removed</li>
  <li>Missing values filled</li>
  <li>Invalid rows removed</li>
</ul>

<hr>

<h2>🔄 Transformations (PART A)</h2>

<ul>
  <li>Creates a new <strong>total</strong> column = price × quantity</li>
  <li>Groups by product / category / item</li>
  <li>Aggregates total_sales, avg_total, count_rows</li>
  <li>Filters positive totals only</li>
  <li>Sorts by total</li>
</ul>

<p>Output file generated:</p>
<code>cleaned_output.csv</code>

<hr>

<h2>🤖 AI Integration (PART B)</h2>

<p>Default backend: <strong>Gemini</strong></p>

<p>AI provides:</p>

<ul>
  <li>Dataset summary</li>
  <li>Pattern recognition</li>
  <li>Anomaly detection</li>
  <li>Business recommendations</li>
</ul>

<p>Set API key in <code>.env</code>:</p>

<pre>
GEMINI_API_KEY=your_api_key_here
</pre>

<p>Includes robust error handling for:</p>

<ul>
  <li>Missing / invalid API key</li>
  <li>No internet</li>
  <li>Rate limits</li>
</ul>

<hr>

<h2>📊 Visualization</h2>

<p>Generates a bar chart:</p>

<ul>
  <li><code>top_products.png</code></li>
</ul>

<p>Shows top products/categories by total sales.</p>

<hr>

<h2>📄 PDF Report Export</h2>

<p>PDF includes:</p>

<ul>
  <li>Cleaning summary</li>
  <li>Transformations summary</li>
  <li>Grouped data preview</li>
  <li>AI insights</li>
  <li>Chart image (if present)</li>
</ul>

<p>Exported as:</p>
<code>report.pdf</code>

<hr>

<h2>🖥️ CLI Menu</h2>

<p>Run the script to open the interactive menu:</p>

<pre>
python data_ai_automator.py
</pre>

<p>Menu options:</p>

<ol>
  <li>Process Data (full pipeline)</li>
  <li>Generate AI report only</li>
  <li>Export PDF only</li>
  <li>Exit</li>
</ol>

<h3>⚡ Auto Mode</h3>

<pre>
python data_ai_automator.py --auto --input sample.csv
</pre>

<hr>

<h2>🛠️ Installation</h2>

<pre>
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
</pre>

<p>Add your Gemini API key:</p>

<pre>
GEMINI_API_KEY=your_key_here
</pre>

<hr>

<h2>▶️ How to Run</h2>

<h3>Menu Mode</h3>
<pre>python data_ai_automator.py</pre>

<h3>Auto Mode</h3>
<pre>python data_ai_automator.py --auto --input sample.csv</pre>

<hr>

<h2>📌 Outputs Generated</h2>

<ul>
  <li>cleaned_output.csv</li>
  <li>top_products.png</li>
  <li>report.pdf</li>
</ul>

<hr>

<h2>📚 Key Learnings</h2>

<ul>
  <li>Multi-format data handling</li>
  <li>Generalized cleaning system</li>
  <li>AI-driven insights</li>
  <li>PDF report automation</li>
  <li>End-to-end automated pipelines</li>
</ul>

<hr>

<div align="center">
  <h3>⭐ If you found this project helpful, consider giving it a star!</h3>
</div>
