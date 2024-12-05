import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';

void main() {
  runApp(const MyApp());
}

///
/// Dieses Beispiel zeigt ein pseudo-Terminal, das einige der im Python-Skript
/// beschriebenen Funktionen via GitHub-API in Dart nachempfindet.
///

// Hier deinen GitHub-Personal-Access-Token einsetzen.
// In einer echten App von Nutzer via Eingabe erfragen.
const GITHUB_TOKEN = "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";

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Pseudo-Terminal Demo',
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: Colors.black,
      ),
      home: const TerminalScreen(),
    );
  }
}

class TerminalScreen extends StatefulWidget {
  const TerminalScreen({super.key});

  @override
  State<TerminalScreen> createState() => _TerminalScreenState();
}

class _TerminalScreenState extends State<TerminalScreen> {
  final TextEditingController _controller = TextEditingController();
  final List<TerminalLine> _lines = [];
  bool _isProcessing = false;

  // Der aktuell genutzte Repo-Name und Owner (wird aus dem Token bestimmt)
  String? _currentRepoName;
  String? _githubUsername;

  @override
  void initState() {
    super.initState();
    _printAsciiArt();
    _printLine("Willkommen im pseudo-Terminal!", color: Colors.green);
    _printLine("Geben Sie 'help' ein, um Befehle zu sehen.", color: Colors.green);
    _fetchUsername();
  }

  Future<void> _fetchUsername() async {
    // GitHub API um den User herauszufinden
    final response = await http.get(
      Uri.parse('https://api.github.com/user'),
      headers: _headers(),
    );
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      _githubUsername = data["login"];
      _printLine("Angemeldet als: $_githubUsername", color: Colors.cyan);
    } else {
      _printLine("Fehler beim Laden des Usernames. Bitte Token prüfen.", color: Colors.red);
    }
  }

  Map<String, String> _headers() {
    return {
      'Authorization': 'token $GITHUB_TOKEN',
      'Accept': 'application/vnd.github.v3+json'
    };
  }

  void _printAsciiArt() {
    List<String> asciiArt = [
      " __  __           _        ____              _       _ _             ",
      "|  \\/  | __ _  __| | ___  | __ ) _   _      | |_   _| (_) __ _ _ __  ",
      "| |\\/| |/ _` |/ _` |/ _ \\ |  _ \\| | | |  _  | | | | | | |/ _` | '_ \\ ",
      "| |  | | (_| | (_| |  __/ | |_) | |_| | | |_| | |_| | | | (_| | | | |",
      "|_|  |_|\\__,_|\\__,_|\\___| |____/ \\__, |  \\___/ \\__,_|_|_|\\__,_|_| |_|",
      "                                 |___/                               ",
    ];

    List<Color> rainbowColors = [
      Colors.red, Colors.yellow, Colors.green, Colors.cyan, Colors.blue, Colors.purple
    ];

    for (var line in asciiArt) {
      List<InlineSpan> spans = [];
      for (int i = 0; i < line.length; i++) {
        String char = line[i];
        if (char.trim().isEmpty) {
          spans.add(TextSpan(text: char, style: const TextStyle(color: Colors.white)));
        } else {
          spans.add(TextSpan(text: char, style: TextStyle(color: rainbowColors[i % rainbowColors.length])));
        }
      }
      _lines.add(TerminalLine.rich(TextSpan(children: spans)));
    }
    setState(() {});
  }

  void _printLine(String text, {Color color = Colors.white}) {
    _lines.add(TerminalLine(text, color: color));
    setState(() {});
  }

  void _onSubmit(String value) async {
    if (value.trim().isEmpty) {
      _controller.clear();
      return;
    }
    _printLine("\$ $value", color: Colors.cyan);
    _controller.clear();

    setState(() {
      _isProcessing = true;
    });
    await _handleCommand(value);
    setState(() {
      _isProcessing = false;
    });
  }

  Future<void> _handleCommand(String input) async {
    final parts = input.trim().split(' ');
    final command = parts.isNotEmpty ? parts[0] : '';
    final args = parts.length > 1 ? parts.sublist(1) : [];

    switch (command) {
      case 'help':
        _printLine("Verfügbare Befehle:", color: Colors.green);
        _printLine(" help                    - Zeige diese Hilfe an");
        _printLine(" createrepo <name>       - Erstelle ein neues Repo auf GitHub");
        _printLine(" repo <name>             - Verwende ein bestehendes Repo");
        _printLine(" upload                  - Lade ein Dummy-Projekt hoch (Datei ins Repo schreiben)");
        _printLine(" addworkflow             - Lege Workflow-Datei im Repo an");
        _printLine(" setpermissions          - Setze Actions Permissions auf write");
        _printLine(" deleteoldruns           - Lösche alte Workflow Runs");
        _printLine(" triggerbuild            - Löst den Workflow Dispatch aus");
        _printLine(" waitbuild               - Warte auf Build-Abschluss (polling)");
        _printLine(" fetchipa                - Lade IPA aus letztem Release herunter (Simulation)");
        _printLine(" clear                   - Leere das Terminal");
        break;
      case 'clear':
        _lines.clear();
        setState(() {});
        break;
      case 'createrepo':
        if (args.isEmpty) {
          _printLine("Fehler: Bitte einen Reponamen angeben.", color: Colors.red);
        } else {
          await _createRepo(args[0]);
        }
        break;
      case 'repo':
        if (args.isEmpty) {
          _printLine("Fehler: Bitte Repo-Namen angeben.", color: Colors.red);
        } else {
          await _useRepo(args[0]);
        }
        break;
      case 'upload':
        await _uploadProject();
        break;
      case 'addworkflow':
        await _addWorkflowFile();
        break;
      case 'setpermissions':
        await _setWorkflowPermissions();
        break;
      case 'deleteoldruns':
        await _deleteOldWorkflowRuns();
        break;
      case 'triggerbuild':
        await _triggerWorkflowDispatch();
        break;
      case 'waitbuild':
        await _waitForWorkflowCompletion();
        break;
      case 'fetchipa':
        await _fetchIPA();
        break;
      default:
        if (command.isNotEmpty) {
          _printLine("Unbekannter Befehl: $command", color: Colors.red);
        }
    }
  }

  Future<void> _createRepo(String name) async {
    if (_githubUsername == null) {
      _printLine("Fehler: Kein GitHub-Username bekannt. Token ok?", color: Colors.red);
      return;
    }

    _printLine("Erstelle Repo '$name'...", color: Colors.yellow);
    final response = await http.post(
      Uri.parse('https://api.github.com/user/repos'),
      headers: _headers(),
      body: jsonEncode({
        "name": name,
        "private": false,
        "auto_init": false
      })
    );

    if (response.statusCode == 201) {
      _printLine("✔ Repository '$name' erfolgreich erstellt.", color: Colors.green);
      _currentRepoName = name;
    } else {
      _printLine("Fehler beim Erstellen des Repos: ${response.body}", color: Colors.red);
    }
  }

  Future<void> _useRepo(String name) async {
    if (_githubUsername == null) {
      _printLine("Fehler: Kein GitHub-Username.", color: Colors.red);
      return;
    }

    _printLine("Prüfe ob Repo '$name' existiert...", color: Colors.yellow);
    final response = await http.get(
      Uri.parse('https://api.github.com/repos/$_githubUsername/$name'),
      headers: _headers(),
    );

    if (response.statusCode == 200) {
      _printLine("✔ Repository '$name' gefunden.", color: Colors.green);
      _currentRepoName = name;
    } else {
      _printLine("Repo '$name' nicht gefunden: ${response.body}", color: Colors.red);
    }
  }

  Future<void> _uploadProject() async {
    if (_currentRepoName == null) {
      _printLine("Kein Repo ausgewählt. Bitte zuerst 'repo <name>' oder 'createrepo <name>' ausführen.", color: Colors.red);
      return;
    }

    _printLine("Lade Dummy-Projektdatei hoch...", color: Colors.yellow);

    // Wir erstellen/aktualisieren die Datei 'main.dart' im Repo unter Pfad 'lib/main.dart'.
    // Zuerst brauchen wir den SHA, falls die Datei schon existiert.
    final filePath = 'lib/main.dart';
    final getFileResponse = await http.get(
      Uri.parse('https://api.github.com/repos/$_githubUsername/$_currentRepoName/contents/$filePath'),
      headers: _headers(),
    );

    String? sha;
    if (getFileResponse.statusCode == 200) {
      final data = jsonDecode(getFileResponse.body);
      sha = data["sha"];
    }

    // Inhalt der Datei (einfacher Dummy-Inhalt):
    final content = base64Encode(utf8.encode("// Dummy Dart file\nvoid main() {}"));

    final putResponse = await http.put(
      Uri.parse('https://api.github.com/repos/$_githubUsername/$_currentRepoName/contents/$filePath'),
      headers: _headers(),
      body: jsonEncode({
        "message": "Initial commit of main.dart",
        "content": content,
        if (sha != null) "sha": sha
      }),
    );

    if (putResponse.statusCode == 201 || putResponse.statusCode == 200) {
      _printLine("✔ Datei main.dart erfolgreich hochgeladen.", color: Colors.green);
    } else {
      _printLine("Fehler beim Hochladen: ${putResponse.body}", color: Colors.red);
    }
  }

  Future<void> _addWorkflowFile() async {
    if (_currentRepoName == null) {
      _printLine("Kein Repo ausgewählt.", color: Colors.red);
      return;
    }

    _printLine("Füge Workflow-Datei hinzu...", color: Colors.yellow);

    final workflowContent = _getWorkflowYaml("FlutterIpaExport.ipa");
    final content = base64Encode(utf8.encode(workflowContent));

    final filePath = '.github/workflows/build_ios.yml';
    // Prüfen ob Datei existiert
    final getResp = await http.get(
      Uri.parse('https://api.github.com/repos/$_githubUsername/$_currentRepoName/contents/$filePath'),
      headers: _headers(),
    );
    String? sha;
    if (getResp.statusCode == 200) {
      final data = jsonDecode(getResp.body);
      sha = data["sha"];
    }

    final putResp = await http.put(
      Uri.parse('https://api.github.com/repos/$_githubUsername/$_currentRepoName/contents/$filePath'),
      headers: _headers(),
      body: jsonEncode({
        "message": "Add/Update iOS Build Workflow",
        "content": content,
        if (sha != null) "sha": sha
      }),
    );

    if (putResp.statusCode == 201 || putResp.statusCode == 200) {
      _printLine("✔ Workflow-Datei erfolgreich angelegt.", color: Colors.green);
    } else {
      _printLine("Fehler beim Anlegen der Workflow-Datei: ${putResp.body}", color: Colors.red);
    }
  }

  Future<void> _setWorkflowPermissions() async {
    if (_currentRepoName == null) {
      _printLine("Kein Repo ausgewählt.", color: Colors.red);
      return;
    }
    _printLine("Setze Workflow Permissions auf Write...", color: Colors.yellow);

    final url = 'https://api.github.com/repos/$_githubUsername/$_currentRepoName/actions/permissions';
    final resp = await http.put(
      Uri.parse(url),
      headers: _headers(),
      body: jsonEncode({
        "enabled": true,
        "allowed_actions": "all",
        "permissions": {
          "contents": "write"
        }
      }),
    );

    if (resp.statusCode == 200 || resp.statusCode == 204) {
      _printLine("✔ Permissions erfolgreich gesetzt.", color: Colors.green);
    } else {
      _printLine("Fehler beim Setzen der Permissions: ${resp.body}", color: Colors.red);
    }
  }

  Future<void> _deleteOldWorkflowRuns() async {
    if (_currentRepoName == null) {
      _printLine("Kein Repo ausgewählt.", color: Colors.red);
      return;
    }

    _printLine("Lösche alte Workflow Runs...", color: Colors.yellow);
    final runsUrl = 'https://api.github.com/repos/$_githubUsername/$_currentRepoName/actions/runs';

    final runsResp = await http.get(Uri.parse(runsUrl), headers: _headers());
    if (runsResp.statusCode == 200) {
      final data = jsonDecode(runsResp.body);
      final runs = data["workflow_runs"] as List;
      for (var run in runs) {
        final runId = run["id"];
        final deleteResp = await http.delete(
          Uri.parse('https://api.github.com/repos/$_githubUsername/$_currentRepoName/actions/runs/$runId'),
          headers: _headers(),
        );
        if (deleteResp.statusCode == 204) {
          _printLine("✔ Workflow Run $runId gelöscht.", color: Colors.green);
        } else {
          _printLine("Fehler beim Löschen von Run $runId: ${deleteResp.body}", color: Colors.red);
        }
      }
      if (runs.isEmpty) {
        _printLine("Keine alten Runs vorhanden.", color: Colors.green);
      }
    } else {
      _printLine("Fehler beim Abrufen der Runs: ${runsResp.body}", color: Colors.red);
    }
  }

  Future<void> _triggerWorkflowDispatch() async {
    if (_currentRepoName == null) {
      _printLine("Kein Repo ausgewählt.", color: Colors.red);
      return;
    }

    _printLine("Trigger Workflow Dispatch...", color: Colors.yellow);

    // Unser Workflow heisst build_ios.yml laut _getWorkflowYaml
    final url = 'https://api.github.com/repos/$_githubUsername/$_currentRepoName/actions/workflows/build_ios.yml/dispatches';

    final resp = await http.post(
      Uri.parse(url),
      headers: _headers(),
      body: jsonEncode({
        "ref": "main"
      }),
    );

    if (resp.statusCode == 204) {
      _printLine("✔ Workflow-Dispatch ausgelöst.", color: Colors.green);
    } else {
      _printLine("Fehler beim Triggern: ${resp.body}", color: Colors.red);
    }
  }

  Future<void> _waitForWorkflowCompletion() async {
    if (_currentRepoName == null) {
      _printLine("Kein Repo ausgewählt.", color: Colors.red);
      return;
    }

    _printLine("Warte auf Abschluss des Builds...", color: Colors.yellow);

    final start = DateTime.now();
    final timeout = Duration(minutes: 5);
    while (DateTime.now().difference(start) < timeout) {
      await Future.delayed(Duration(seconds: 10));

      final runsResp = await http.get(
        Uri.parse('https://api.github.com/repos/$_githubUsername/$_currentRepoName/actions/runs?branch=main'),
        headers: _headers(),
      );
      if (runsResp.statusCode == 200) {
        final data = jsonDecode(runsResp.body);
        final runs = data["workflow_runs"] as List;
        if (runs.isNotEmpty) {
          final latestRun = runs.first;
          final status = latestRun["status"];
          final conclusion = latestRun["conclusion"];

          _printLine("Run ${latestRun["id"]} Status: $status", color: Colors.cyan);

          if (status == "completed") {
            if (conclusion == "success") {
              _printLine("✔ Build erfolgreich abgeschlossen.", color: Colors.green);
              return;
            } else {
              _printLine("✘ Build fehlgeschlagen: $conclusion", color: Colors.red);
              return;
            }
          }
        } else {
          _printLine("Keine Runs vorhanden, warte weiter...", color: Colors.yellow);
        }
      } else {
        _printLine("Fehler beim Abrufen der Runs: ${runsResp.body}", color: Colors.red);
        return;
      }
    }

    _printLine("✘ Timeout: Build nicht abgeschlossen.", color: Colors.red);
  }

  Future<void> _fetchIPA() async {
    if (_currentRepoName == null) {
      _printLine("Kein Repo ausgewählt.", color: Colors.red);
      return;
    }

    _printLine("Hole Releases...", color: Colors.yellow);
    final releasesResp = await http.get(
      Uri.parse('https://api.github.com/repos/$_githubUsername/$_currentRepoName/releases'),
      headers: _headers(),
    );
    if (releasesResp.statusCode == 200) {
      final releases = jsonDecode(releasesResp.body) as List;
      if (releases.isEmpty) {
        _printLine("✘ Keine Releases gefunden.", color: Colors.red);
        return;
      }
      final latestRelease = releases.first;
      final assets = latestRelease["assets"] as List;
      final ipaAsset = assets.firstWhere((a) => a["name"].toString().endsWith(".ipa"), orElse: () => null);
      if (ipaAsset == null) {
        _printLine("✘ Keine IPA im letzten Release gefunden.", color: Colors.red);
        return;
      }
      final downloadUrl = ipaAsset["browser_download_url"];
      _printLine("✔ IPA Download URL: $downloadUrl", color: Colors.green);

      // Simulierter Download:
      _printLine("Lade IPA herunter (Simulation)...", color: Colors.yellow);
      await Future.delayed(Duration(seconds: 2));
      _printLine("✔ IPA erfolgreich heruntergeladen.", color: Colors.green);
    } else {
      _printLine("Fehler beim Laden der Releases: ${releasesResp.body}", color: Colors.red);
    }
  }

  String _getWorkflowYaml(String ipaName) {
    return """
name: iOS Build

on:
  workflow_dispatch:

permissions:
  contents: write

jobs:
  build-ios:
    name: iOS Build
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3

      - uses: subosito/flutter-action@v2
        with:
          channel: 'stable'
          architecture: x64
      - run: flutter pub get

      - run: pod repo update
        working-directory: ios

      - run: flutter build ios --release --no-codesign

      - run: mkdir Payload
        working-directory: build/ios/iphoneos

      - run: mv Runner.app/ Payload
        working-directory: build/ios/iphoneos

      - name: Zip output
        run: zip -qq -r -9 $ipaName Payload
        working-directory: build/ios/iphoneos

      - name: Upload binaries to release
        uses: svenstaro/upload-release-action@v2
        with:
          repo_token: \${{ secrets.GITHUB_TOKEN }}
          file: build/ios/iphoneos/$ipaName
          tag: v1.0
          overwrite: true
          body: "This is first release"
""";
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Pseudo-Terminal"),
        backgroundColor: Colors.black,
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: ListView.builder(
                key: ValueKey(_lines.length),
                itemCount: _lines.length,
                itemBuilder: (context, index) {
                  final line = _lines[index];
                  if (line.textSpan != null) {
                    return RichText(
                      text: line.textSpan!,
                    );
                  } else {
                    return Text(
                      line.text,
                      style: TextStyle(color: line.color, fontFamily: 'monospace'),
                    );
                  }
                },
              ),
            ),
            Container(
              color: Colors.black,
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      onSubmitted: (value) => _onSubmit(value),
                      style: const TextStyle(color: Colors.white, fontFamily: 'monospace'),
                      decoration: const InputDecoration(
                        hintText: 'Befehl eingeben...',
                        hintStyle: TextStyle(color: Colors.grey),
                        border: InputBorder.none,
                      ),
                    ),
                  ),
                  if (_isProcessing)
                    const Padding(
                      padding: EdgeInsets.only(left: 8.0),
                      child: SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class TerminalLine {
  final String text;
  final Color color;
  final TextSpan? textSpan;

  TerminalLine(this.text, {this.color = Colors.white}) : textSpan = null;
  TerminalLine.rich(this.textSpan)
      : text = '',
        color = Colors.white;
}
