// Quick and dirty SockJS benchmark

package main

import (
	"websocket"
	"fmt"
	"time"
	"strconv"
	"strings"
	"json"
	"rand"
	"flag"
	"runtime"
)

// Dummy SockJS client implementation
func SockJSClient(client_id int) {
	ws, err := websocket.Dial("ws://localhost:8080/echo/0/0/websocket", "", "http://localhost/");
	if err != nil {
		panic("Dial: " + err.String())
	}

	var msg = make([]byte, 512)
	n, err := ws.Read(msg)
	if err != nil {
		panic("Read: " + err.String())
	}

	handshake := string(msg[0:n])
	if handshake != "o" {
		panic("Invalid SockJS handshake: " + handshake)
	}

	var avg_ping int64
	var min_ping int64
	var max_ping int64
	my_packets := 0
	packets := 0
	last_check := time.Nanoseconds()

	for {
		val := fmt.Sprintf("[\"%d,%d\"]", client_id, time.Nanoseconds())
		ws.Write([]byte(val))

		for {
			n, err = ws.Read(msg)
			if err != nil {
				panic("Read failed: " + err.String())
			}

			data := string(msg[0:n])
			if data[0] == 'a' {
				dec := json.NewDecoder(strings.NewReader(data[1:]))

				var v []string

				if err := dec.Decode(&v); err != nil {
					panic("JSON decode failed: " + err.String())
					return
				}

				packets += 1

				got_response := false

				for _,k := range v {
					parts := strings.Split(k, ",")

					cid, _ := strconv.Atoi(parts[0])
					if client_id == cid {
						stamp, _ := strconv.Atoi64(parts[1])
						delta := time.Nanoseconds() - stamp

						if (max_ping < delta) {
							max_ping = delta
						}
						if (min_ping > delta) {
							min_ping = delta
						}

						avg_ping = (avg_ping + delta) / 2
						my_packets += 1

						got_response = true
					}
				}

				if got_response {
					break
				}
			} else
			if data[0] == 'c' {
				return
			}
		}

		// If one second passed, drop statistics
		now := time.Nanoseconds()
		if now - last_check > 1000000000 {
			fmt.Printf("pps: %d, mpps: %d, avg_ping: %d, min_ping: %d, max_ping: %d\n",
						packets,
						my_packets,
						avg_ping / 1000000,
						min_ping / 1000000,
						max_ping / 1000000)

			my_packets = 0
			packets = 0
			last_check = now

			min_ping = ^int64(0)
			max_ping = 0
		}
	}
}

var numCores = flag.Int("n", 1, "num of CPU cores to use")
var numClients = flag.Int("c", 1, "num of clients")

// Entry point
func main() {
	flag.Parse()

	rand.Seed(time.Nanoseconds())

	runtime.GOMAXPROCS(*numCores)

	for i := 0; i < *numClients; i++ {
		go SockJSClient(rand.Int())
	}

	for { time.Sleep(1000000000); }
}
