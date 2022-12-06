let aliveSecond = 0;
let heartbeatRate = 1000;
let myChannel = "dmn-channel";
let pubnub;

let letScannedId;
const setupPubNub = () =>{
    pubnub = new PubNub({
        publishKey: 'pub-c-6df66f48-e71d-41ea-a2a7-d696bda5a561',
        subscribeKey: 'sub-c-5efa4cb5-6f01-42ea-a6ac-98b3dccd764a',
        userId: "serverJS"
    });

    const listener = {
        status: (statusEvent) => {
            if(statusEvent.category === "PNConnectedCategory"){
                console.log("Connected");
            }
        },
        message: (messageEvent) => {

			if(messageEvent.message['finger_scanner_new'])
			{
				console.log(messageEvent.message['finger_scanner_new']);
				lastScannedId = messageEvent.message['finger_scanner_new']
				document.getElementById("fingerprint-box").value = lastScannedId;
			}

        },
        presence: (presenceEvent) => {
            //Handle presence
        }
    };
    pubnub.addListener(listener);

    //subscribe to a channel
    pubnub.subscribe({channels: [myChannel]});
};

const publishMessage = async (message) => {
    const publishPayload = {
        channel : myChannel,
        message: {
            title: "Command",
            description: message
        }
    };
    await pubnub.publish(publishPayload);
}

function keepAlive()
{
	fetch('/keep_alive')
	.then(response=>{
		if(response.ok){
			let date = new Date();
			aliveSecond = date.getTime();
			return response.json();
		}
		throw new Error("Server offline")
	})
	.then(responseJson => {
		if(responseJson.motion === 1){
			document.getElementById("motion_id").innerHTML = "Motion Detected";
		}
		else
		{

			document.getElementById("motion_id").innerHTML = "No Motion Detected";
		}

		console.log(responseJson)})
	.catch(error => console.log(error));
	setTimeout('keepAlive()', heartbeatRate);
}


function time()
{
	let d = new Date();
	let currentSec = d.getTime();
	console.log(currentSec - aliveSecond)
	if(currentSec - aliveSecond > heartbeatRate + 1000)
	{

		document.getElementById("Connection_id").innerHTML = "DEAD";
	}
	else
	{
		document.getElementById("Connection_id").innerHTML = "ALIVE";
	}
	setTimeout('time()', 1000);
}

function handleClick(cb){
	if(cb.checked){
		value = "ON";
	}else{
		value = "OFF";
	}
	publishMessage(cb.id+"-"+value);
}

function registerPrint()
{

	publishMessage("CMD2")
	console.log()
}
function clearPrints(){

	publishMessage("CMD4")
}

window.onload = setupPubNub;
