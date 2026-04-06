#include <iostream>
#include <vector>

int main() {
    int matrix_size = 1048576; // 4MB matrix
    int vector_size = 32768;   // 128kB vector

    std::vector<int> streaming_matrix(matrix_size, 1);
    std::vector<int> hot_vector(vector_size, 2);

    long long sum = 0;

    for (int iter = 0; iter < 10; iter++) {
        for (int i = 0; i < matrix_size; i++) {
            sum += streaming_matrix[i]; 
        }
        for (int j = 0; j < 5; j++) {
            for (int k = 0; k < vector_size; k++) {
                sum += hot_vector[k]; 
            }
        }
    }

    std::cout << "Execution Output: " << sum << std::endl;
    return 0;
}
