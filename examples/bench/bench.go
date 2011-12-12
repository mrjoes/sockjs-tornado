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
	"math"
)

type Stats struct
{
	start_time int64
	end_time int64

	client_id int

	avg_ping int64
	min_ping int64
	max_ping int64

	sent int
	recv int

	my_packets int
}

func NewStats() Stats {
	n := Stats{}
	n.sent = 0
	n.recv = 0
	n.min_ping = ^int64(0)
	return n
}

// Warmup time in seconds
const WARMUP_TIME int64 = 1
// Test time in seconds
const TEST_TIME int64 = 10

func SockJSClient(client_id int, cs chan *Stats) {
	// Error handler
	defer func() {
		if r := recover(); r != nil {
			cs <- nil
		}
	}()

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

						stats.avg_ping = (stats.avg_ping + delta) / 2
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
	ramps := [9]int{5,25,50,100,150,200,300,500,1000}
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
		errors := 0

		for j := 0; j < num_clients; j++ {
			stats := <-cs

			if stats != nil {
				seconds := float64(stats.end_time - stats.start_time) / 1000000000

				total_sent += float64(stats.sent) / seconds
				total_recv += float64(stats.recv) / seconds

				if math.IsNaN(total_sent) {
					fmt.Printf("--> %d, %d, %f\n", stats.sent, stats.recv, seconds)
				}
			} else
			{
				errors += 1
			}
		}

		fmt.Printf("clients: %d, sent: %f, recv: %f, errors: %d\n", num_clients, total_sent, total_recv, errors)
	}
}
