#include <iostream>
#include <queue>
#include <cmath>
#include <vector>
#include <tuple>

struct Particle {
    double x, y, z;
    double vx, vy, vz;
    double radius;
};

double collision_time(const Particle& p1, const Particle& p2) {
    double rx = p1.x - p2.x;
    double ry = p1.y - p2.y;
    double rz = p1.z - p2.z;
    double vx = p1.vx - p2.vx;
    double vy = p1.vy - p2.vy;
    double vz = p1.vz - p2.vz;

    double a = vx * vx + vy * vy + vz * vz;
    double b = 2 * (rx * vx + ry * vy + rz * vz);
    double c = rx * rx + ry * ry + rz * rz - (p1.radius + p2.radius) * (p1.radius + p2.radius);

    double discriminant = b * b - 4 * a * c;
    if (discriminant < 0) return INFINITY;

    double t1 = (-b - sqrt(discriminant)) / (2 * a);
    double t2 = (-b + sqrt(discriminant)) / (2 * a);

    if (t1 > 0) return t1;
    if (t2 > 0) return t2;
    return INFINITY;
}

int main() {
    std::vector<Particle> particles = {
        {0, 0, 0, 1, 0, 0, 0.5},
        {1, 0, 0, -1, 0, 0, 0.5}
    };

    // Min-heap priority queue
    std::priority_queue<std::tuple<double, int, int>, std::vector<std::tuple<double, int, int>>, std::greater<>> heap;

    for (int i = 0; i < particles.size(); ++i) {
        for (int j = i + 1; j < particles.size(); ++j) {
            double t = collision_time(particles[i], particles[j]);
            if (t < INFINITY) {
                heap.push(std::make_tuple(t, i, j));
            }
        }
    }

    while (!heap.empty()) {
        auto [t, i, j] = heap.top();
        heap.pop();
        std::cout << "Collision between " << i << " and " << j << " at time " << t << "\n";
    }

    return 0;
}

