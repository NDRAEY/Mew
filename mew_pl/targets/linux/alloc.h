#pragma once

#include <stdlib.h>
#include <stdint.h>

void* __allocator_alloc(size_t bytes);
void __allocator_free(void* ptr);

inline void* __allocator_alloc(size_t bytes) {
	return malloc(bytes);
}

inline void __allocator_free(void* ptr) {
	free(ptr);
}
