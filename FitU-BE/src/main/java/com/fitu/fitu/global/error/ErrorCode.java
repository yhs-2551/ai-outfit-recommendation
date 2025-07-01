package com.fitu.fitu.global.error;

import lombok.Getter;

@Getter
public enum ErrorCode {

    /* COMMON ERROR */
    INTERNAL_SERVER_ERROR(500, "COMMON001", "Internal Server Error"),
    INVALID_INPUT_VALUE(400, "COMMON002", "Invalid Input Value"),
    ENTITY_NOT_FOUND(400, "COMMON003", "Entity Not Found"),

    /* USER ERROR */
    USER_NOT_FOUND(400, "USER001", "User Not Found"),
    /* CLOTHES ERROR */
    CLOTHES_NOT_FOUND_BY_ID(404, "CLOTHES001", "Clothes not found"),
    CLOTHES_ACCESS_DENIED(403, "CLOTHES002", "Access to this clothing item is denied"),
    CLOTHES_AI_ANALYSIS_FAILED(500, "CLOTHES004", "Failed to analyze clothes with AI"),
    CLOTHES_IMAGE_PROCESSING_ERROR(500, "CLOTHES005", "Error occurred while processing clothes image"),
    CLOTHES_INVALID_CLOTHES_COMBINATION(400, "CLOTHES006", "Invalid clothes combination"),
    CLOTHES_INVALID_CLOTHES_TYPE(400, "CLOTHES007", "Not a clothes image"),
    CLOTHES_ATTRIBUTES_REQUIRED(400, "CLOTHES008", "Clothes attributes are required"),

    /* S3 ERROR */
    S3_URL_INVALID(400, "S3001", "Invalid S3 URL format"),
    S3_FILE_READ_ERROR(500, "S3002", "Error reading S3 file"),
    S3_UPLOAD_ERROR(500, "S3002", "Failed to upload file to S3"),
    S3_DELETE_ERROR(500, "S3003", "Failed to delete file from S3"),
    
    CLOTHES_NOT_FOUND(400, "CLOTHES001", "Clothes Not Found"),
    /* RECOMMENDATION ERROR */
    NO_RECOMMENDATION(500, "RECOMMENDATION001", "No Recommendation"),
    AI_RECOMMENDATION_SERVER_ERROR(500, "RECOMMENDATION002", "AI Recommendation Server Error"),

    /* S3 ERROR */
    S3_UPLOAD_FAILED(500, "S3001", "Failed to upload file to S3"),
    S3_DELETE_FAILED(500, "S3002", "Failed to delete file from S3"),
    S3_COPY_FAILED(500, "S3003", "Failed to copy file from S3"),
    S3_INVALID_URL(400, "S3004", "Invalid S3 file URL"),

    /* File ERROR */
    FILE_NOT_FOUND(400, "FILE001", "File Not Found"),
    FILE_INVALID_EXTENSION(400, "FILE002", "Invalid File Extension");


    private final int status;
    private final String code;
    private final String message;

    ErrorCode(final int status, final String code, final String message) {
        this.status = status;
        this.code = code;
        this.message = message;
    }
}
