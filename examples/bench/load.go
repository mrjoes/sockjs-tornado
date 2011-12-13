// Quick and dirty SockJS benchmark
// Creates several connections to the server, where each connection
// sends ping and waits for its own pong. One pong was received, it will
// send another ping.

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
	"syscall"
)

type Stats struct
{
	start_time int64
	end_time int64

	client_id int

	min_ping int64
	max_ping int64

	sent int
	recv int

	my_packets int
}

func NewStats() Stats {
	n := Stats{}
	n.min_ping = ^int64(0)
	return n
}

// Warmup time in seconds
const WARMUP_TIME int64 = 1
// Test time in seconds
const TEST_TIME int64 = 10

func SockJSClient(client_id int, cs chan *Stats) {
	ws, err := websocket.Dial("ws://localhost:8080/broadcast/0/0/websocket", "", "http://localhost/");

	// Error handler
	defer func() {
		if ws != nil {
			ws.Close()
		}

		if r := recover(); r != nil {
			cs <- nil
		}
	}()	

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

	stats := NewStats()
	start_time := time.Nanoseconds()
	end_time := start_time + TEST_TIME * 1000000000
	stats.start_time = start_time

	for ; time.Nanoseconds() < end_time; {
		val := fmt.Sprintf("[\"%d,%d\"]", client_id, time.Nanoseconds())
		n, err = ws.Write([]byte(val))
		if n != len(val) || err != nil {
			panic("Send failed!")
		}

		stats.sent += 1

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

				stats.recv += 1

				got_response := false

				for _,k := range v {
					parts := strings.Split(k, ",")

					cid, _ := strconv.Atoi(parts[0])
					if client_id == cid {
						stamp, _ := strconv.Atoi64(parts[1])
						delta := time.Nanoseconds() - stamp

						if (stats.max_ping < delta) {
							stats.max_ping = delta
						}
						if (stats.min_ping > delta) {
							stats.min_ping = delta
						}

						stats.my_packets += 1

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
	}

	// Output statistics
	stats.end_time = time.Nanoseconds()
	cs <- &stats
}

var numCores = flag.Int("n", 1, "num of CPU cores to use")
//var numClients = flag.Int("c", 1, "num of clients")

// Entry point
func main() {
	flag.Parse()

	rand.Seed(time.Nanoseconds())

	runtime.GOMAXPROCS(*numCores)

	// Number of clients to add for each ramp
	ramps := []int{5,25,50,100,150,200,300,500,1000}
	//ramps := [3]int{200,300,500}

	for i := 0; i < len(ramps); i++ {
		num_clients := ramps[i]

		cs := make(chan *Stats)
		for j := 0; j < num_clients; j++ {
			go SockJSClient(rand.Int(), cs)
		}

		// Collect stats
		var total_sent float64 = 0
		var total_recv float64 = 0
		var min_ping int64 = ^int64(0)
		var max_ping int64 = 0
		var avg_ping float64 = 0

		errors := 0

		for j := 0; j < num_clients; j++ {
			stats := <-cs

			if stats != nil {
				seconds := float64(stats.end_time - stats.start_time) / 1000000000

				total_sent += float64(stats.sent) / seconds
				total_recv += float64(stats.recv) / seconds

				if min_ping > stats.min_ping {
					min_ping = stats.min_ping
				}
				if max_ping < stats.max_ping {
					max_ping = stats.max_ping
				}

				avg_ping += float64((max_ping - min_ping) / 1000000) / seconds
			} else
			{
				errors += 1
			}
		}

		flt_clients := float64(num_clients)
		avg_ping /= flt_clients

		fmt.Printf("clients: %d, sent: %f, recv: %f, min_ping: %d, max_ping: %d, avg_ping: %f, errors: %d\n",
					num_clients,
					total_sent,
					total_recv,
					min_ping / 1000000,
					max_ping / 1000000,
					avg_ping,
					errors)

		// Give it time to settle
		syscall.Sleep(5 * 1000000000)
	}
}
