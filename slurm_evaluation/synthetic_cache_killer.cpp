#include <iostream>
#include <vector>

// 4MB Streaming matrix to heavily thrash the LRU cache
#define MATRIX_BYTES (1024 * 1024 * 4) 
// 128kB Reusable priority vector (which fits perfectly into a 1MB L2 cache if protected)
#define VECTOR_BYTES (1024 * 128)      

int main() {
    volatile long long sum = 0;
    
    // Allocate mathematical arrays
    int matrix_size = MATRIX_BYTES / sizeof(int);
    int vector_size = VECTOR_BYTES / sizeof(int);
    
    std::vector<int> streaming_matrix(matrix_size, 1);
    std::vector<int> hot_vector(vector_size, 2);

    std::cout << "Commencing Synthetic Cache-Killer Execution..." << std::endl;

    // Execute 10 loops of a massive 4MB memory sweep
    // This is engineered specifically so that Memory L2 Miss Latency completely
    // dominates the CPU pipeline, mimicking a purely memory-bound architecture workload.
    for (int iter = 0; iter < 10; iter++) {
        for (int i = 0; i < matrix_size; i++) {
            // Unpredictable contiguous streaming fetch (Pollutes pure LRU)
            sum += streaming_matrix[i]; 
            
            // Highly reused target fetch (Adaptive Bypass will lock this in memory safely)
            sum += hot_vector[i % vector_size]; 
        }
    }
    
    std::cout << "Synthetic execution completed successfully. Control Sum: " << sum << std::endl;
    return 0;
}
