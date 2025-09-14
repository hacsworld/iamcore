package main

import (
	"bufio"
	"bytes"
	"crypto/ed25519"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"time"

	"github.com/gorilla/websocket"
)

var (
	deviceID    string
	privateKey  ed25519.PrivateKey
	publicKey   ed25519.PublicKey
	wsConn      *websocket.Conn
	coreProcess *exec.Cmd
)

type PairRequest struct {
	Code     string `json:"code"`
	PubKey   string `json:"pubkey"`
	Platform string `json:"platform"`
}

type PairResponse struct {
	DeviceID  string `json:"device_id"`
	Token     string `json:"token"`
	WSURL     string `json:"ws_url"`
	ExpiresIn int    `json:"expires_in,omitempty"`
}

func keyPath() (priv, pub string) {
	home, _ := os.UserHomeDir()
	dir := filepath.Join(home, ".hacs")
	_ = os.MkdirAll(dir, 0o700)
	return filepath.Join(dir, "device.key"), filepath.Join(dir, "device.pub")
}

func loadOrGenerateKeys() {
	privF, pubF := keyPath()
	if pk, err := os.ReadFile(privF); err == nil {
		privateKey = ed25519.PrivateKey(pk)
		if pb, err := os.ReadFile(pubF); err == nil {
			publicKey = ed25519.PublicKey(pb)
			fmt.Println("🔑 Loaded existing device keys")
			return
		}
	}
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		log.Fatal("Failed to generate keys:", err)
	}
	publicKey, privateKey = pub, priv
	_ = os.WriteFile(privF, privateKey, 0o600)
	_ = os.WriteFile(pubF, publicKey, 0o600)
	fmt.Println("🔑 Generated new device keys")
}

func startCore() {
	corePath := filepath.Join(".", "core", "app.py")
	if _, err := os.Stat(corePath); os.IsNotExist(err) {
		log.Printf("⚠️  Core not found at %s", corePath)
		return
	}

	coreProcess = exec.Command("python", corePath)
	coreProcess.Dir = "./core"
	coreProcess.Stdout = os.Stdout
	coreProcess.Stderr = os.Stderr

	if err := coreProcess.Start(); err != nil {
		log.Printf("⚠️  Could not start core: %v", err)
		return
	}
	fmt.Println("🚀 Started local HACS core on http://127.0.0.1:8000")
	time.Sleep(2 * time.Second)
}

func pairDevice() {
	reader := bufio.NewReader(os.Stdin)
	fmt.Print("📱 Enter 6-digit pairing code: ")
	code, _ := reader.ReadString('\n')
	if len(code) > 0 && code[len(code)-1] == '\n' {
		code = code[:len(code)-1]
	}
	if len(code) != 6 {
		log.Fatal("❌ Invalid code format. Must be 6 digits.")
	}

	pubKeyHex := hex.EncodeToString(publicKey)
	platform := runtime.GOOS + "/" + runtime.GOARCH

	req := PairRequest{
		Code:     code,
		PubKey:   pubKeyHex,
		Platform: platform,
	}

	jsonData, _ := json.Marshal(req)
	resp, err := http.Post("https://pair.hacs.world/pair/finish", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		log.Fatal("❌ Pairing failed:", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		log.Fatal("❌ Pairing failed with status:", resp.Status)
	}

	var pairResp PairResponse
	if err := json.NewDecoder(resp.Body).Decode(&pairResp); err != nil {
		log.Fatal("❌ Failed to decode response:", err)
	}

	deviceID = pairResp.DeviceID
	fmt.Printf("✅ Paired successfully! Device ID: %s\n", deviceID)
	fmt.Printf("🌐 Connecting to %s...\n", pairResp.WSURL)

	connectWS(pairResp.WSURL, pairResp.Token)
}

func connectWS(url, token string) {
	backoff := time.Second
	for {
		dialer := websocket.Dialer{}
		headers := http.Header{"Authorization": []string{"Bearer " + token}}
		conn, _, err := dialer.Dial(url, headers)
		if err != nil {
			log.Printf("❌ WS connection failed: %v. Retrying in %v...", err, backoff)
			time.Sleep(backoff)
			if backoff < 30*time.Second {
				backoff *= 2
			}
			continue
		}
		wsConn = conn
		fmt.Println("🌐 Connected to HACS cloud gateway")

		for {
			var msg struct {
				Type  string `json:"type"`
				ReqID string `json:"req_id"`
				Text  string `json:"text"`
			}
			if err := conn.ReadJSON(&msg); err != nil {
				log.Printf("❌ WS read error: %v. Reconnecting...", err)
				break
			}

			switch msg.Type {
			case "ping":
				_ = conn.WriteJSON(map[string]string{"type": "pong"})
			case "act":
				go processIntent(msg.ReqID, msg.Text)
			default:
				log.Printf("⚠️  Unknown message type: %s", msg.Type)
			}
		}
		conn.Close()
	}
}

func processIntent(reqID, text string) {
	fmt.Printf("🤖 Processing intent: %s\n", text)

	payload := []byte(fmt.Sprintf(`{"text": "%s"}`, text))
	resp, err := http.Post("http://127.0.0.1:8000/act", "application/json", bytes.NewBuffer(payload))

	var result json.RawMessage
	if err != nil {
		log.Printf("❌ Local core error: %v", err)
		result, _ = json.Marshal(map[string]string{"error": "Local core unavailable"})
	} else {
		defer resp.Body.Close()
		if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
			log.Printf("❌ Failed to decode local response: %v", err)
			result, _ = json.Marshal(map[string]string{"error": "Invalid response from local core"})
		}
	}

	if wsConn != nil {
		response := map[string]interface{}{
			"type":    "act_result",
			"req_id":  reqID,
			"result":  result,
			"local":   true,
		}
		if err := wsConn.WriteJSON(response); err != nil {
			log.Printf("❌ Failed to send response: %v", err)
		}
	}
}

func main() {
	fmt.Println(`
🎯 HACS Local AI Agent 🎯
Connecting your personal AI to the cloud...
	`)
	loadOrGenerateKeys()
	startCore()
	pairDevice()

	select {}
}
