## Setup Meta Webhook

### Variables .env
META_VERIFY_TOKEN=your_random_token
META_ACCESS_TOKEN=your_page_access_token
META_WHATSAPP_PHONE_ID=your_phone_number_id

### Webhook URL to register in Meta App Dashboard
https://api.ether.care/meta/webhook

### Subscribed fields
WhatsApp: messages
Instagram: messages, messaging_postbacks
Facebook: messages, messaging_postbacks

### Test verification
curl "https://api.ether.care/meta/webhook?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=test123"
Expected response: test123
