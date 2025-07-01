package com.fitu.fitu.infra.s3;

import com.fitu.fitu.global.error.ErrorCode;
import com.fitu.fitu.global.error.exception.BusinessException;
import com.fitu.fitu.global.error.exception.SystemException;
import io.awspring.cloud.s3.S3Exception;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.CopyObjectRequest;
import software.amazon.awssdk.services.s3.model.DeleteObjectRequest;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;

import java.io.IOException;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.UUID;

@Slf4j
@RequiredArgsConstructor
@Service
public class S3Uploader {

    @Value("${spring.cloud.aws.s3.bucket}")
    private String bucket;

    @Value("${spring.cloud.aws.region.static}")
    private String region;

    private final S3Client s3Client;

    public String upload(final String path, final MultipartFile file) {
        try {
            final String objectKey = generateKey(path, file);

            final PutObjectRequest putRequest = PutObjectRequest.builder()
                    .bucket(bucket)
                    .key(objectKey)
                    .contentType(file.getContentType())
                    .build();

            s3Client.putObject(putRequest, RequestBody.fromInputStream(file.getInputStream(), file.getSize()));

            return generateS3Url(objectKey);
        } catch (S3Exception | IOException e) {
            throw new SystemException(ErrorCode.S3_UPLOAD_FAILED);
        }
    }

    public void delete(final String s3Url) {
        try {
            final String objectKey = extractKey(s3Url);

            final DeleteObjectRequest deleteRequest = DeleteObjectRequest.builder()
                    .bucket(bucket)
                    .key(objectKey)
                    .build();

            s3Client.deleteObject(deleteRequest);
        } catch (Exception e) {
            throw new SystemException(ErrorCode.S3_DELETE_FAILED);
        }
    }

    public String copy(final String s3Url, final String targetPath) {
        final String objectKey = extractKey(s3Url);

        final String destinationKey = targetPath + objectKey.substring(objectKey.lastIndexOf("/") + 1);

        final CopyObjectRequest copyRequest = CopyObjectRequest.builder()
                .sourceBucket(bucket)
                .sourceKey(objectKey)
                .destinationBucket(bucket)
                .destinationKey(destinationKey)
                .build();
        try {
            s3Client.copyObject(copyRequest);

            return generateS3Url(destinationKey);
        } catch (S3Exception e) {
            throw new SystemException(ErrorCode.S3_COPY_FAILED);
        }
    }

    private String generateKey(final String path, final MultipartFile file) {
        final String extension = StringUtils.getFilenameExtension(file.getOriginalFilename());
        final String fileName = UUID.randomUUID() + "." + extension;

        return path + fileName;
    }

    private String extractKey(final String s3Url) {
        try {
            final URI uri = new URI(s3Url);

            return uri.getPath().substring(1);
        } catch (URISyntaxException e) {
            throw new BusinessException(ErrorCode.S3_INVALID_URL);
        }
    }

    private String generateS3Url(final String objectKey) {
        return "https://" + bucket + ".s3." + region + ".amazonaws.com/" + objectKey;
    }
}