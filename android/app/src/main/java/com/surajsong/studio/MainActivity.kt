package com.surajsong.studio

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.FilterChip
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    SurajSongHome()
                }
            }
        }
    }
}

@Composable
private fun SurajSongHome() {
    var topic by remember { mutableStateOf("") }
    var language by remember { mutableStateOf("Bengali") }
    var status by remember { mutableStateOf("Ready to create your first song") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Text("SurajSong", style = MaterialTheme.typography.headlineLarge)
        Text(
            "AI Bengali & Hindi Music Studio",
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.primary
        )
        Text("Create original lyrics, music, AI vocals and music videos from your Android phone.")

        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("Create a new song", style = MaterialTheme.typography.titleLarge)
                OutlinedTextField(
                    value = topic,
                    onValueChange = { topic = it },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text("Song topic or idea") },
                    placeholder = { Text("Example: হারিয়ে যাওয়া ভালোবাসা") },
                    minLines = 3
                )
                Text("Language")
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    FilterChip(
                        selected = language == "Bengali",
                        onClick = { language = "Bengali" },
                        label = { Text("বাংলা") }
                    )
                    FilterChip(
                        selected = language == "Hindi",
                        onClick = { language = "Hindi" },
                        label = { Text("हिन्दी") }
                    )
                }
                Text("AI will choose the genre, mood, tempo and singer. Target duration: 3–5 minutes.")
                Button(
                    onClick = {
                        status = if (topic.isBlank()) {
                            "Please enter a song topic first."
                        } else {
                            "Project brief saved locally. AI generation service will be connected in the next milestone."
                        }
                    },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Create Song")
                }
            }
        }

        Text("Your studio", style = MaterialTheme.typography.titleLarge)
        StudioFeatureCard("My Songs", "Generated songs and MP3 exports")
        StudioFeatureCard("AI Music Video", "Create images, one thumbnail and an MP4")
        StudioFeatureCard("YouTube Upload", "Connect your channel and manage uploads")
        Spacer(Modifier.height(8.dp))
        Text(status, style = MaterialTheme.typography.bodyMedium)
        Text(
            "Free-first project: generation providers will be connected after checking their free limits and model licenses.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
private fun StudioFeatureCard(title: String, description: String) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium)
            Text(description, style = MaterialTheme.typography.bodyMedium)
        }
    }
}
