const path = require( 'path' );
const express = require( 'express' );
const socketIO = require( 'socket.io' );
const {env} = require('process');




var connectCounter = 0

// create an express app
const app = express();

// send 'index.html' from the current directory
app.get( '/', ( request, response ) => {
  response.sendFile( path.resolve( __dirname, 'src/index.html' ), {
    headers: {
      'Content-Type': 'text/html',
    }
  } );
} );

app.get( '/clock', ( request, response ) => {
  response.sendFile( path.resolve( __dirname, 'src/clock.html' ), {
    headers: {
      'Content-Type': 'text/html',
    }
  } );
} );

app.get( '/radio', ( request, response ) => {
  response.sendFile( path.resolve( __dirname, 'src/radio.html' ), {
    headers: {
      'Content-Type': 'text/html',
    }
  } );
} );


// send asset files
app.use( express.static('src' ) );
//app.use( '/assets/', express.static( path.resolve( __dirname, 'node_modules/socket.io-client/dist' ) ) );

// server listens on port 80
const server = app.listen( 80, () => console.log( 'Express server started!' ) );

// create a WebSocket server
const io = socketIO( server );

// listen for connection
console.log( 'socket listening' );
io.on( 'connection', ( client ) => {
  console.log( 'Socket client connection:', client.id );
  connectCounter++;
  console.log( 'Socket client count:', connectCounter );
  //led_connect( 1 );
  client.emit('intro', { message: "yo!" });
  //client.emit('led-status', { r: red_led_state(), y: yellow_led_state(), g: green_led_state() }); // transmit the LED status to this client
  //io.emit('spinme', { message: "ya!" });

  // listen to `led-toggle` event
  client.on( 'spinme', ( data ) => {
    console.log( 'Received spin!.' );
    //toggle( data.c, data.b ); // change LEDs
    io.emit('spinme', { message: "ya!" }); // transmit the LED status back to all clients
  } );

  client.on( 'tune', ( data ) => {
    console.log( 'Received tune!' );
    //toggle( data.c, data.b ); // change LEDs
    io.emit('tune', { message: data }); // transmit the LED status back to all clients
  } );

 client.on( 'info', ( data ) => {
    console.log( 'Received info!' );
    //toggle( data.c, data.b ); // change LEDs
    io.emit('info', { message: data }); // transmit the LED status back to all clients
  } );

  client.on('disconnect', function() {
      //socket.emit('disconnect')
      connectCounter--;
      console.log('Socket client disconnected: ', client.id );
      if (connectCounter == 0) {
          console.log('All clients disconnected.')
          //led_connect( 0 );
      }
  });

} );
