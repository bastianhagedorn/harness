//
// Created by Bastian Hagedorn
//

#ifndef EXECUTOR_CONVOLUTIONSEPARABLEY_HARNESS_H
#define EXECUTOR_CONVOLUTIONSEPARABLEY_HARNESS_H

#include <cmath>
#include <condition_variable>
#include <functional>
#include <iostream>
#include <mutex>
#include <queue>
#include <thread>

#include "opencl_utils.h"
#include "run.h"
#include "utils.h"

using namespace std;

void set_kernel_args(const shared_ptr<Run> run, const cl::Buffer &grid_dev,
                     const cl::Buffer &weights_dev,
                     const cl::Buffer &output_dev, const size_t M,
                     const size_t N) {
  unsigned i = 0;
  run->getKernel().setArg(i++, grid_dev);
  run->getKernel().setArg(i++, weights_dev);
  run->getKernel().setArg(i++, output_dev);
  // provide extra local memory args if existing
  for (const auto &local_arg : run->extra_local_args)
    run->getKernel().setArg(i++, local_arg);
  run->getKernel().setArg(i++, static_cast<int>(M));
  run->getKernel().setArg(i++, static_cast<int>(N));
}

void compute_gold(const size_t M, const size_t N, Matrix<float> &grid,
                  Matrix<float> &weights, Matrix<float> &gold,
                  const std::string &grid_file, const std::string &weights_file,
                  const std::string &gold_file) {

  // init weights -- currently hardcoded for 3
  for (unsigned x = 0; x < 3; ++x) {
    weights[x] = x * 1.0f;
  }

  // init grid
  for (unsigned y = 0; y < N; ++y)
    for (unsigned x = 0; x < N; ++x) {
      grid[y * N + x] = (((y * N + x) % 8) + 1) * 1.0f;
    }

  // compute gold
  std::cout << "compute gold" << std::endl;
  for (unsigned y = 0; y < M; ++y) {
    for (unsigned x = 0; x < N; ++x) {

      float sum = 0.0f;
      for (int i = -1; i < 2; ++i) {
        int posY = y + i;

        // clamp boundary
        posY = max(0, posY);
        posY = min(static_cast<int>(M - 1), posY);

        int coord = posY * N + x;
        float weight = weights[(i + 1)];

        sum += grid[coord] * weight;
      }
      unsigned position = y * N + x;
      gold[position] = sum;
    }
  }

  File::save_input(gold, gold_file);
  File::save_input(grid, grid_file);
  File::save_input(weights, weights_file);
}

void run_harness(std::vector<std::shared_ptr<Run>> &all_run, const size_t M,
                 const size_t N, const std::string &grid_file,
                 const std::string &gold_file, const std::string &weights_file,
                 const bool force, const bool threaded, const bool binary) {

  if (binary)
    std::cout << "Using precompiled binaries" << std::endl;

  // M rows, N columns
  Matrix<float> grid(M * N);
  Matrix<float> gold(M * N);
  Matrix<float> weights(3);

  // use existing grid, weights and gold or init them
  if (File::is_file_exist(gold_file) && File::is_file_exist(grid_file) &&
      File::is_file_exist(weights_file)) {
    std::cout << "use existing grid, weights and gold" << std::endl;
    File::load_input(gold, gold_file);
    File::load_input(grid, grid_file);
    File::load_input(weights, weights_file);
  } else {
    std::cout << "init grid and weights and compute gold" << std::endl;
    compute_gold(M, N, grid, weights, gold, grid_file, weights_file, gold_file);
  }

  // validation function
  auto validate = [&](const std::vector<float> &output) {
    if (gold.size() != output.size())
      return false;
    for (unsigned i = 0; i < gold.size(); ++i) {
      auto x = gold[i];
      auto y = output[i];

      if (abs(x - y) > 0.001f * max(abs(x), abs(y))) {
        cerr << "at " << i << ": " << x << "=/=" << y << std::endl;
        return false;
      }
    }
    return true;
  };

  // Allocating buffers
  const size_t buf_size = grid.size() * sizeof(float);
  const size_t weights_size = weights.size() * sizeof(float);
  cl::Buffer grid_dev =
      OpenCL::alloc(CL_MEM_READ_ONLY | CL_MEM_COPY_HOST_PTR, buf_size,
                    static_cast<void *>(grid.data()));
  cl::Buffer weights_dev =
      OpenCL::alloc(CL_MEM_READ_ONLY | CL_MEM_COPY_HOST_PTR, weights_size,
                    static_cast<void *>(weights.data()));
  cl::Buffer output_dev = OpenCL::alloc(CL_MEM_READ_WRITE, buf_size);

  // multi-threaded exec
  if (threaded) {
    std::mutex m;
    std::condition_variable cv;

    bool done = false;
    bool ready = false;
    std::queue<shared_ptr<Run>> ready_queue;

    // compilation thread
    auto compilation_thread = std::thread([&] {
      for (auto &r : all_run) {
        if (r->compile(binary)) {
          std::unique_lock<std::mutex> locker(m);
          ready_queue.push(r);
          ready = true;
          cv.notify_one();
        }
      }
    });

    auto execute_thread = std::thread([&] {
      shared_ptr<Run> r = nullptr;
      while (!done) {
        {
          std::unique_lock<std::mutex> locker(m);
          while (!ready && !done)
            cv.wait(locker);
        }

        while (!ready_queue.empty()) {
          {
            std::unique_lock<std::mutex> locker(m);
            r = ready_queue.front();
            ready_queue.pop();
          }

          set_kernel_args(r, grid_dev, weights_dev, output_dev, M, N);
          OpenCL::executeRun<float>(*r, output_dev, M * N, validate);
        }
      }
    });

    compilation_thread.join();
    done = true;
    cv.notify_one();
    execute_thread.join();
  }
  // single threaded exec
  else {
    for (auto &r : all_run) {
      if (r->compile(binary)) {
        set_kernel_args(r, grid_dev, weights_dev, output_dev, M, N);
        OpenCL::executeRun<float>(*r, output_dev, M * N, validate);
      }
    }
  }
};

#endif // EXECUTOR_CONVOLUTIONSEPARABLEY_HARNESS_H
