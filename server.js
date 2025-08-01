const express = require('express');
const fs = require('fs');
const path = require('path');
const bodyParser = require('body-parser');

const app = express();
const PORT = 3000;

app.use(bodyParser.json());
app.use(express.static('public')); // 정적 HTML 제공

const dataPath = path.join(__dirname, 'data', 'consults.json');

app.post('/api/consult', (req, res) => {
    const newEntry = req.body;

    fs.readFile(dataPath, 'utf8', (err, data) => {
        let consults = [];
        if (!err && data) consults = JSON.parse(data);
        consults.push({ ...newEntry, timestamp: new Date().toISOString() });

        fs.writeFile(dataPath, JSON.stringify(consults, null, 2), (err) => {
            if (err) return res.status(500).json({ message: '저장 실패' });
            res.json({ message: '저장 완료' });
        });
    });
});

app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});
