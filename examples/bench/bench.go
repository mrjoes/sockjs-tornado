package main

import (
	"websocket"
	"runtime"
	"flag"
	"rand"
	"fmt"
	"time"
	"syscall"
	"json"
	"strings"
	"strconv"
)

// SockJS client
type Stats struct
{
	sent int
	recv int

	start_time int64
	end_time int64

	min_ping int64
	max_ping int64
}

func newStats() *Stats {
	n := new(Stats)
	n.min_ping = ^int64(0)
	return n
}

func clientReceiver(ch chan string, ws *websocket.Conn) {
	var b = make([]byte, 512)

	for {
		n, err := ws.Read(b);

		if err != nil {
			ch <- ""
			break
		}

		ch <- string(b[0:n])
	}
}

func clientSender(client_id int, ch chan bool, result chan *Stats) {
	ws, err := websocket.Dial("ws://localhost:8080/broadcast/0/0/websocket", "", "http://localhost/");

	defer func() {
		if ws != nil {
			ws.Close()
		}

		if r := recover(); r != nil {
			result <- nil
		}
	}()

	if err != nil {
		panic("Dial: " + err.String())
	}

	reader := make(chan string)

	go clientReceiver(reader, ws)

	if handshake := <-reader; handshake != "o" {
		panic("Invalid handshake!")
	}

	ch <- true

	need_finish := false
	num_pending := 0

	stats := newStats()
	stats.start_time = time.Nanoseconds()

	for ; !need_finish || num_pending > 0; {
		select {
		case msg := <-reader:
			if msg == "" {
				break
			}

			if msg[0] == 'a' {
				dec := json.NewDecoder(strings.NewReader(msg[1:]))

				var v []string

				if err := dec.Decode(&v); err != nil {
					panic("JSON decode failed: " + err.String())
				}

				stats.recv += 1

				got_response := false

				for _,k := range v {
					parts := strings.Split(k, ",")

					cid, _ := strconv.Atoi(parts[0])
					if client_id == cid {
						stamp, _ := strconv.Atoi64(parts[1])

						dt := time.Nanoseconds() - stamp

						if stats.min_ping > dt {
							stats.min_ping = dt
						}
						if stats.max_ping < dt {
							stats.max_ping = dt
						}
						num_pending -= 1

						got_response = true
					}
				}

				if got_response {
					break
				}
			} else
			if msg[0] == 'c' {
				panic("Got disconnect packet!")
			}
		case evt := <-ch:
			if evt {
				stamp := time.Nanoseconds()

				msg := fmt.Sprintf("[\"%d,%d\"]", client_id, stamp)
				ws.Write([]byte(msg))

				stats.sent += 1

				num_pending += 1
			} else
			{
				need_finish = true
			}
		}
	}

	stats.end_time = time.Nanoseconds()

	result <- stats
}

var numCores = flag.Int("n", 1, "num of CPU cores to use")
var msgPerSec = flag.Int64("m", 100, "number of messages per second")
var msgTotal = flag.Int("t", 10000, "number of messages to send")

// Entry point
func main() {
	rand.Seed(time.Nanoseconds())

	flag.Parse()
	runtime.GOMAXPROCS(*numCores)

	// Number of clients to add for each ramp
	ramps := []int{5,25,50,100,200,300,500,1000}

	for i := 0; i < len(ramps); i++ {
		num_clients := ramps[i]

		channels := make([]chan bool, num_clients)
		stats := make(chan *Stats)

		for j := 0; j < num_clients; j++ {
			channels[j] = make(chan bool)
			go clientSender(rand.Int(), channels[j], stats)
		}

		// Wait for all clients to start
		for j := 0; j < num_clients; j++ {
			<- channels[j]
		}		

		var msg_delay int64 = 1000000000 / *msgPerSec
		var time_slot int64 = msg_delay

		for j := 0; j < *msgTotal; j++ {
			start := time.Nanoseconds()

			channels[j % num_clients] <- true

			delta_ts := time.Nanoseconds()
			time_slot -= (delta_ts - start)
			if time_slot > 0 {
				syscall.Sleep(time_slot)
			}

			delta_end := time.Nanoseconds() - delta_ts
			time_slot += (msg_delay - delta_end)
		}

		for j := 0; j < num_clients; j++ {
			channels[j] <- false
		}

		// Collect stats
		var total_sent float64 = 0
		var total_recv float64 = 0
		var min_ping int64 = ^int64(0)
		var max_ping int64 = 0
		var avg_ping float64 = 0

		errors := 0

		for j := 0; j < num_clients; j++ {
			data := <-stats

			if data != nil {
				seconds := float64(data.end_time - data.start_time) / 1000000000

				total_sent += float64(data.sent) / seconds
				total_recv += float64(data.recv) / seconds

				if min_ping > data.min_ping {
					min_ping = data.min_ping
				}
				if max_ping < data.max_ping {
					max_ping = data.max_ping
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
	}
}
