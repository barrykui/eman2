FILE(GLOB testprograms "${CMAKE_CURRENT_SOURCE_DIR}/*.py")
INSTALL(FILES ${testprograms}
  DESTINATION    test/rt/pyem
)
