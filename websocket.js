const { WebSocketServer } = require('ws');

const server = new WebSocketServer({ host: '0.0.0.0', port: 8081 });

let clients = [];
let lastDataRequestTime = 0;
const dataRequestInterval = 5000;


server.on('connection', ws => {
    console.log('New client connected');
    clients.push(ws);

    ws.on('message', message => {
        console.log(`Received: ${message}`);

        if (message === 'GET_DATA') {
            const currentTime = Date.now();
            if (currentTime - lastDataRequestTime >= dataRequestInterval) {
                const sensorData = JSON.stringify({
                    humidity: (Math.random() * 100).toFixed(2),
                    soil_moisture: (Math.random() * 100).toFixed(2)
                });
                ws.send(sensorData);
                lastDataRequestTime = currentTime;
            } else {
                console.log("Data requested too frequently.");
            }
        } else {
            clients.forEach(client => {
                if (client !== ws && client.readyState === WebSocket.OPEN) {
                    client.send(message);
                }
            });
        }
    });

    ws.on('close', () => {
        console.log('Client disconnected');
        clients = clients.filter(client => client !== ws);
    });

    ws.on('error', error => {
        console.error(`WebSocket error: ${error}`);
    });

    const interval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
            ws.ping();
        } else {
            clearInterval(interval);
        }
    }, 10000);
});

server.on('listening', () => {
    console.log('WebSocket server started at ws://192.168.1.10:8081');
});

server.on('error', error => {
    console.error(`Server error: ${error}`);
});





