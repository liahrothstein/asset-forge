// forge.cpp — оркестратор конвейера
// Сборка: cl /std:c++17 /EHsc /O2 forge.cpp /Fe:forge.exe
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

struct Job { std::string name, prompt; };

struct Config {
    int target_tris = 20000;
    int bake_res    = 1024;
};

static bool run(const std::string& cmd) {
    std::cout << "  CMD: " << cmd << "\n";
    return std::system(cmd.c_str()) == 0;
}

static std::vector<Job> readQueue(const fs::path& p) {
    std::vector<Job> jobs;
    std::ifstream f(p);
    for (std::string line; std::getline(f, line); ) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty() || line[0] == '#') continue;
        auto bar = line.find('|');
        if (bar == std::string::npos) continue;
        std::string name = line.substr(0, bar);
        // имя становится именем файла и аргументом bat — пробелы недопустимы
        if (name.find(' ') != std::string::npos) {
            std::cout << "  ! Имя с пробелом пропущено: " << name << "\n";
            continue;
        }
        jobs.push_back({ name, line.substr(bar + 1) });
    }
    return jobs;
}

int main(int argc, char** argv) {
    Config cfg;
    fs::path queuePath = (argc > 1) ? argv[1] : "queue.txt";
    for (auto d : { "work/ref", "work/raw", "work/logs", "assets" })
        fs::create_directories(d);

    for (auto& bat : { "run_sd.bat", "run_meshes.bat", "run_blender.bat" })
        if (!fs::exists(bat)) {
            std::cout << "Не найден " << bat << " — создайте его рядом с forge.exe\n";
            return 1;
        }

    auto jobs = readQueue(queuePath);
    std::cout << "В очереди: " << jobs.size() << " ассетов\n";

        // ---------- ФАЗА 1: референсы ----------
    {
        int pending = 0;
        for (auto& j : jobs)
            if (!fs::exists("work/ref/" + j.name + ".png")) ++pending;

        if (pending > 0) {
            {
                std::ofstream out("work/pending.txt");
                for (auto& j : jobs)
                    if (!fs::exists("work/ref/" + j.name + ".png"))
                        out << j.name << "|" << j.prompt << "\n";
            }   // ← файл ЗАКРЫТ и данные гарантированно на диске ЗДЕСЬ

            std::cout << "[1/3] Референсы (SD): " << pending << " шт...\n";
            if (!run("run_sd.bat"))
                std::cout << "  ! Фаза 1 упала, см. work/logs/images.log\n";
        } else std::cout << "[1/3] Референсы готовы, пропускаю\n";
    }

    // ---------- ФАЗА 2: меши ----------
    {
        bool pending = false;
        for (auto& j : jobs)
            if (fs::exists("work/ref/" + j.name + ".png") &&
                !fs::exists("work/raw/" + j.name + ".obj")) pending = true;
        if (pending) {
            std::cout << "[2/3] Image-to-3D (TripoSR)...\n";
            if (!run("run_meshes.bat"))
                std::cout << "  ! Фаза 2 упала, см. work/logs/meshes.log\n";
        } else std::cout << "[2/3] Пропускаю (референсы ещё не готовы)\n";
    }

    // ---------- ФАЗА 3: Blender ----------
    std::ofstream manifest("manifest.csv", std::ios::app);
    int ok = 0, fail = 0;
    for (auto& j : jobs) {
        fs::path raw = fs::path("work") / "raw" / (j.name + ".obj");
        fs::path dst = fs::path("assets") / (j.name + ".glb");
        if (!fs::exists(raw) || fs::exists(dst)) continue;

        std::cout << "[3/3] " << j.name << " -> Blender...\n";
        std::string log = std::string("work\\logs\\") + j.name + ".log";
        std::string cmd = "run_blender.bat " + raw.string() + " " + dst.string() + " "
                + std::to_string(cfg.target_tris) + " "
                + std::to_string(cfg.bake_res) + " " + log
                + " work\\ref\\" + j.name + ".png";
        bool success = run(cmd) && fs::exists(dst);
        manifest << j.name << ";" << j.prompt << ";"
                 << (success ? "OK" : "FAIL") << "\n";
        success ? ++ok : ++fail;
    }
    std::cout << "\nГотово. OK: " << ok << ", FAIL: " << fail << "\n";
    return 0;
}