#include <iostream>
#include <vector>

int main() {
    int matrix_size = 1048576; // 4MB matrix, easily flushes 1MB LRU
    int vector_size = 32768;   // 128kB vector, fits nicely in L2
    
    std::vector<int> streaming_matrix(matrix_size, 1);
    std::vector<int> hot_vector(vector_size, 2);
    
    long long sum = 0;
    
    for (int iter = 0; iter < 20; iter++) {
        

        for (int i = 0; i < matrix_size; i++) {
            streaming_matrix[i] ^= (i % 256);
            sum += streaming_matrix[i]; 
        }

        for (int k = 0; k < vector_size; k++) {
            int val = hot_vector[k];
            
            for (int w = 0; w < 50; w++) {
                val = (val ^ (w * 7)) + 1;
            }
            
            hot_vector[k] = val;
            sum += val;
        }
    }

    std::cout << "Execution Output: " << sum << std::endl;
    return 0;
}
