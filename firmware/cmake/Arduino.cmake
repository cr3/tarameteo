function(add_arduino_upload_target TARGET_NAME SKETCH_DIR FQBN PORT)
    add_custom_target(${TARGET_NAME}
        COMMAND arduino-cli compile --fqbn ${FQBN} --libraries ${CMAKE_SOURCE_DIR}/lib ${CMAKE_SOURCE_DIR}/${SKETCH_DIR}
        COMMAND arduino-cli upload -p ${PORT} --fqbn ${FQBN} ${CMAKE_SOURCE_DIR}/${SKETCH_DIR}
        COMMENT "Building and uploading Arduino sketch from ${CMAKE_SOURCE_DIR}/${SKETCH_DIR}"
    )
endfunction()

function(add_arduino_monitor_target TARGET_NAME PORT BAUDRATE)
    add_custom_target(${TARGET_NAME}
        COMMAND arduino-cli monitor -p ${PORT} -c baudrate=${BAUDRATE}
        COMMENT "Opening Serial Monitor on ${PORT} at ${BAUDRATE} baud"
        VERBATIM
    )
endfunction()
