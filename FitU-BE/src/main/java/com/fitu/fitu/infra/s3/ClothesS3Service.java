package com.fitu.fitu.infra.s3;

import java.io.IOException;
import java.util.UUID;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import com.fitu.fitu.global.error.ErrorCode;
import com.fitu.fitu.global.error.exception.BusinessException;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.CopyObjectRequest;
import software.amazon.awssdk.services.s3.model.DeleteObjectRequest; 
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import software.amazon.awssdk.services.s3.model.S3Exception;

@Slf4j
@RequiredArgsConstructor
@Service
public class ClothesS3Service {

    @Qualifier("clothesS3Client")
    private final S3Client s3Client;

    @Value("${team3.aws.s3.bucket}")
    private String bucketName;

    @Value("${team3.aws.s3.temp-bucket}")
    private String tempBucketName;

    @Value("${team3.aws.region}")
    private String region;

    public String uploadFile(final MultipartFile file, final String directory) {

        if (file == null || file.isEmpty()) {
            log.error("파일 업로드 실패 - 파일이 비어있거나 null.");
            throw new BusinessException(ErrorCode.INVALID_INPUT_VALUE);
        }
        try {

            final String fileName = directory + "/" + UUID.randomUUID() + "_" + file.getOriginalFilename();

            final PutObjectRequest putObjectRequest = PutObjectRequest.builder()
                    .bucket(bucketName)
                    .key(fileName)
                    .contentType(file.getContentType())
                    .build();

            s3Client.putObject(putObjectRequest,
                    software.amazon.awssdk.core.sync.RequestBody.fromInputStream(
                            file.getInputStream(), file.getSize()));

            final String fileUrl = String.format("https://%s.s3.%s.amazonaws.com/%s",
                    bucketName, region, fileName);

            return fileUrl;

        } catch (S3Exception e) {
            log.error("S3 업로드 실패 - 파일명: {}, S3 오류 코드: {}, 메시지: {}",
                    file.getOriginalFilename(), e.awsErrorDetails().errorCode(), e.getMessage());
            throw new BusinessException(ErrorCode.S3_UPLOAD_ERROR);
        } catch (IOException e) {
            log.error("파일 읽기 실패 - 파일명: {}, 오류: {}", file.getOriginalFilename(), e.getMessage());
            throw new BusinessException(ErrorCode.S3_FILE_READ_ERROR);
        } catch (Exception e) {
            log.error("파일 업로드 중 예상치 못한 오류 발생 - 파일명: {}, 오류: {}",
                    file.getOriginalFilename(), e.getMessage(), e);
            throw e;
        }
    }

    public String moveFileFromTempBucket(final String sourceUrl, final String targetDirectory) {

        try {

            final String sourceKey = extractFileKeyFromUrl(sourceUrl);

            final String fileName = sourceKey.substring(sourceKey.lastIndexOf("/") + 1);

            final String targetKey = targetDirectory + "/" + fileName;

            // 임시 버킷에서 최종 버킷으로 복사, 삭제는 S3 생명주기 사용
            CopyObjectRequest copyObjectRequest = CopyObjectRequest.builder()
                    .sourceBucket(tempBucketName) // 임시 버킷
                    .sourceKey(sourceKey)
                    .destinationBucket(bucketName) // 최종 버킷
                    .destinationKey(targetKey)
                    .build();

            s3Client.copyObject(copyObjectRequest);

            final String newFileUrl = String.format("https://%s.s3.%s.amazonaws.com/%s",
                    bucketName, region, targetKey);

            return newFileUrl;

        } catch (S3Exception e) {
            log.error("버킷 간 파일 이동 실패 - S3 오류 코드: {}, 메시지: {}",
                    e.awsErrorDetails().errorCode(), e.getMessage());
            throw new BusinessException(ErrorCode.S3_UPLOAD_ERROR);
        } catch (Exception e) {
            log.error("파일 이동 중 예상치 못한 오류 발생 - 오류: {}", e.getMessage(), e);
            throw e;
        }
    }

    public void deleteFile(final String fileUrl) {
        try {
            // URL에서 파일 키 추출
            final String fileKey = extractFileKeyFromUrl(fileUrl);

            final DeleteObjectRequest deleteObjectRequest = DeleteObjectRequest.builder()
                    .bucket(bucketName)
                    .key(fileKey)
                    .build();

            s3Client.deleteObject(deleteObjectRequest);

        } catch (S3Exception e) {
            log.error("S3 파일 삭제 실패 - S3 오류 코드: {}, 메시지: {}",
                    e.awsErrorDetails().errorCode(), e.getMessage());
            throw new BusinessException(ErrorCode.S3_DELETE_ERROR);
        } catch (Exception e) {
            log.error("파일 삭제 중 예상치 못한 오류 발생 - 오류: {}", e.getMessage(), e);
            throw e;
        }
    }

    /**
     * 이동 및 생성 후 삭제.
     */
    public String updateFile(final MultipartFile analySisFailureFile, final String analySisSuccessPrevUrl,
            final String dbImageUrl,
            final String targetDirectory, final boolean isAnalySisSuccess) {

        final String updateUrl = !isAnalySisSuccess
                ? uploadFile(analySisFailureFile, targetDirectory)
                : moveFileFromTempBucket(analySisSuccessPrevUrl, targetDirectory);

        deleteFile(dbImageUrl);

        return updateUrl;

    }

    private String extractFileKeyFromUrl(final String fileUrl) {
        try {
            final String[] parts = fileUrl.split(".com/");
            if (parts.length > 1) {
                return parts[1];
            }
            log.error("S3 URL에서 파일 키 추출 실패 - 잘못된 URL 형식");
            throw new BusinessException(ErrorCode.S3_URL_INVALID);
        } catch (Exception e) {
            log.error("S3 URL에서 파일 키 추출 실패 - 오류: {}", e.getMessage(), e);
            throw e;
        }
    }
}